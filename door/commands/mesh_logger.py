import datetime
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from typing import Optional

from pubsub import pub
import sqlite3
from sqlite3 import Cursor
from pydantic import BaseModel
from loguru import logger as log

from . import BaseCommand
from ..models import UserInfo, Message, Position, DeviceMetric, EnvironmentMetric


def insert_node(cursor: Cursor, node: str):
    cursor.execute("INSERT OR IGNORE INTO node VALUES (?)", (node,))


def insert_message(cursor: Cursor, message: Message):
    cursor.execute(
        (
            "INSERT INTO message (timestamp, fromId, toId, payload) "
            "VALUES (datetime(), ?, ?, ?)"
        ),
        (message.fromId, message.toId, message.payload),
    )


def insert_node_info(cursor: Cursor, node_info: UserInfo):
    cursor.execute(
        (
            "INSERT INTO node_info (timestamp, node, longName, shortName, macaddr, hwModel) "
            "VALUES (datetime(), ?, ?, ?, ?, ?)"
        ),
        (
            node_info.id,
            node_info.longName,
            node_info.shortName,
            node_info.macaddr,
            node_info.hwModel,
        ),
    )


def insert_position(cursor: Cursor, position: Position):
    cursor.execute(
        (
            "INSERT INTO position (timestamp, node, latitude, longitude, altitude) "
            "VALUES (datetime(), ?, ?, ?, ?)"
        ),
        (position.id, position.latitude, position.longitude, position.altitude),
    )


def insert_device_metric(cursor: Cursor, device_metric: DeviceMetric):
    cursor.execute(
        (
            "INSERT INTO device_metric "
            "(timestamp, node, batteryLevel, channelUtilization, airUtilTx, uptimeSeconds) "
            "VALUES (datetime(), ?, ?, ?, ?, ?);"
        ),
        (
            device_metric.id,
            device_metric.batteryLevel,
            device_metric.channelUtilization,
            device_metric.airUtilTx,
            device_metric.uptimeSeconds,
        ),
    )


def insert_environment_metric(cursor: Cursor, em: EnvironmentMetric):
    cursor.execute(
        (
            "INSERT INTO environment_metric ("
            "timestamp, node, temperature, relative_humidity, barometric_pressure, "
            "gas_resistance, voltage, current, iaq, distance, "
            "lux, white_lux, ir_lux, uv_lux, wind_direction, "
            "wind_speed, weight, wind_gust, wind_lull"
            ") VALUES ("
            "datetime(), ?, ?, ?, ?, "
            "?, ?, ?, ?, ?,"
            "?, ?, ?, ?, ?,"
            "?, ?, ?, ?"
            ")"
        ),
        (
            em.id,
            em.temperature,
            em.relative_humidity,
            em.barometric_pressure,
            em.gas_resistance,
            em.voltage,
            em.current,
            em.iaq,
            em.distance,
            em.lux,
            em.white_lux,
            em.ir_lux,
            em.uv_lux,
            em.wind_direction,
            em.wind_speed,
            em.weight,
            em.wind_gust,
            em.wind_lull,
        ),
    )


def mesh_logger(db_file: Path, work: Queue, shutdown: Event):
    db = sqlite3.connect(db_file)

    # run
    log.debug("started mesh_logger thread")
    node_id: str
    item: BaseModel
    while not shutdown.is_set():
        try:
            node_id, item = work.get(timeout=1)
        except Empty:
            continue

        # NOTE this is unsafe
        # if something fails and we don't mark the work as done it will hang forever on nice shutdown

        log.debug(f"{type(item).__name__} {item.model_dump(exclude_unset=True)}")
        cursor = db.cursor()

        insert_node(cursor, node_id)

        if type(item) == Position:
            # item.id = node_id
            insert_position(cursor, item)
        elif type(item) == Message:
            # the recipient of this message may not already be in our node table
            insert_node(cursor, item.toId)
            insert_message(cursor, item)
        elif type(item) == UserInfo:
            item.id = node_id
            insert_node_info(cursor, item)
        elif type(item) == DeviceMetric:
            item.id = node_id
            insert_device_metric(cursor, item)
        elif type(item) == EnvironmentMetric:
            item.id = node_id
            insert_environment_metric(cursor, item)
        else:
            log.debug(f"Skipping unknown item: {item}")

        work.task_done()
        cursor.close()
        db.commit()


class MeshLogger(BaseCommand):
    """
    log positions and messages to primary channel
    allow users to query
    """

    command = "log"
    description = "display messages from primary channel"
    # help = "'log next' to view the next page"

    def load(self):
        data_dir: Path = self.get_setting(Path, "data_dir")
        self.db_file = data_dir / "mesh_logger.sqlite"

        # create tables
        db = sqlite3.connect(self.db_file)
        ddl_file = Path(__file__).with_name("mesh_logger.sql")
        db.executescript(ddl_file.open("r").read())
        db.commit()

        # only log packets that are not private to me
        self.me = self.interface.getMyUser()["id"]

        # send work to a thread that writes the DB
        self.work_queue = Queue()
        self.shutdown_event = Event()

        thread = Thread(
            target=mesh_logger,
            args=(self.db_file, self.work_queue, self.shutdown_event),
            name="mesh_logger",
        )
        thread.start()

        pub.subscribe(self.on_data, "meshtastic.receive")

    def invoke(self, msg: str, node: str):
        # shouldn't be a problem connecting from different threads if we are just reading
        db = sqlite3.connect(self.db_file)

        res = db.execute(
            """
            SELECT timestamp, fromId, payload
            FROM message WHERE toId='^all'
            LIMIT 5 OFFSET 0;
            """
        )

        reply = ""
        for row in res.fetchall():
            line = f"{row[0][:-3]} {row[1][-4:]}\n{row[2]}\n\n"
            if len(reply + line) > 200:
                break
            reply += line
        db.close()

        self.send_dm(reply.strip(), node)

    def on_data(self, packet, interface):
        # skip packets sent directly to us

        if "decoded" not in packet:
            log.debug(f"'decoded' not in packet keys: {packet.keys()}")
            return

        unknown = True
        decoded = packet["decoded"]
        fromId = packet["fromId"]
        toId = packet.get("toId", None)

        # skip messages from the device we are connected to
        if fromId == self.me:
            return

        if "portnum" in decoded:
            if decoded["portnum"] == "TELEMETRY_APP":
                unknown = False

                if "deviceMetrics" in decoded["telemetry"]:
                    metric = DeviceMetric(**decoded["telemetry"]["deviceMetrics"])
                    self.work_queue.put((fromId, metric))
                if "environmentMetrics" in decoded["telemetry"]:
                    metric = EnvironmentMetric(
                        **decoded["telemetry"]["environmentMetrics"]
                    )
                    self.work_queue.put((fromId, metric))

            elif decoded["portnum"] == "NODEINFO_APP":
                node_info = UserInfo(**decoded["user"])
                self.work_queue.put((fromId, node_info))
                unknown = False

            elif decoded["portnum"] == "TEXT_MESSAGE_APP":
                # skip messages directly to us
                if toId == self.me:
                    return
                message = Message(
                    fromId=fromId, toId=toId, payload=packet["decoded"]["payload"]
                )
                self.work_queue.put((packet["toId"], message))
                unknown = False

        # position could be attached with other "apps"
        if "position" in decoded:
            pos = decoded["position"]
            if "latitude" in pos and "longitude" in pos:
                position = Position(
                    fromId=fromId,
                    toId=toId,
                    latitude=pos["latitude"],
                    longitude=pos["longitude"],
                    altitude=pos.get("altitude", None),
                )
                self.work_queue.put((fromId, position))
            unknown = False

        if unknown:
            log.debug("unknown packet")
            log.debug(packet)

    def shutdown(self):
        log.debug("Joining work queue..")
        self.work_queue.join()
        log.debug("Setting shutdown event..")
        self.shutdown_event.set()
