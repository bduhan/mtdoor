import datetime
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from typing import Optional

from pubsub import pub
import sqlite3
from pydantic import BaseModel
from loguru import logger as log

from . import BaseCommand, CommandLoadError
from ..models import UserInfo

DDL = [
    """
CREATE TABLE IF NOT EXISTS message (
    timestamp INTEGER,
    fromId TEXT,
    toId TEXT,
    payload TEXT
);
""",
    """
CREATE TABLE IF NOT EXISTS position (
    timestamp INTEGER,
    fromId TEXT,
    latitude REAL,
    longitude REAL,
    altitude INTEGER
);
""",
]


class ShortUserInfo(BaseModel):
    # timestamp: datetime.datetime
    fromId: str
    toId: Optional[str] = None


class Message(ShortUserInfo):
    payload: str


class Position(ShortUserInfo):
    latitude: float
    longitude: float
    altitude: Optional[float] = None


def mesh_logger(db_file: Path, work: Queue, shutdown: Event):
    db = sqlite3.connect(db_file)

    # create tables
    for ddl in DDL:
        db.execute(ddl)
    db.commit()

    # run
    log.debug("started mesh_logger thread")
    while not shutdown.is_set():
        try:
            item: BaseModel = work.get(timeout=1)
        except Empty:
            continue

        log.debug(item)

        if type(item) == Position:
            db.execute(
                (
                    "INSERT INTO position (timestamp, fromId, latitude, longitude) "
                    "VALUES (datetime(), ?, ?, ?)"
                ),
                (item.fromId, item.latitude, item.longitude),
            )
            db.commit()
        elif type(item) == Message:
            db.execute(
                (
                    "INSERT INTO message (timestamp, fromId, toId, payload) "
                    "VALUES (datetime(), ?, ?, ?)"
                ),
                (item.fromId, item.toId, item.payload),
            )
        else:
            log.debug(f"Skipping unknown item: {item}")
            work.task_done()
            continue

        # db.execute(
        #     "INSERT INTO mesh_log (type, timestamp, data) VALUES (?, datetime(), ?)",
        #     (type_str, item.model_dump_json(exclude_none=True, exclude_unset=True)),
        # )
        db.commit()
        # dirty = True

        work.task_done()


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
        self.db_file = data_dir / "mesh_log.sqlite"

        # only log packets that are not private to me
        self.me = self.interface.getMyUser()["id"]

        # send work to a thread that writes the DB
        self.work_queue = Queue()
        self.shutdown_event = Event()

        thread = Thread(
            target=mesh_logger,
            args=(self.db_file, self.work_queue, self.shutdown_event),
        )
        thread.start()

        pub.subscribe(self.on_data, "meshtastic.receive.text")
        pub.subscribe(self.on_data, "meshtastic.receive.position")

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
        if "toId" in packet and packet["toId"] == self.me:
            return

        if "decoded" not in packet:
            log.debug(f"'decoded' not in packet keys: {packet.keys()}")
            return

        decoded = packet["decoded"]
        fromId = packet["fromId"]
        toId = packet.get("toId", None)

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
                self.work_queue.put(position)

        if "payload" in decoded and decoded["portnum"] == "TEXT_MESSAGE_APP":
            message = Message(
                fromId=fromId, toId=toId, payload=packet["decoded"]["payload"]
            )
            self.work_queue.put(message)

    def shutdown(self):
        log.debug("Joining work queue..")
        self.work_queue.join()
        log.debug("Setting shutdown event..")
        self.shutdown_event.set()
