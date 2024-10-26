import sys, time, signal

from loguru import logger as log
from meshtastic.serial_interface import SerialInterface

# from sky import solar_position, moon_phase

from door_manager import DoorManager

from commands import all_commands


# TODO handle other interface types
iface = SerialInterface()
door = DoorManager(iface)
door.add_commands(all_commands)


# handle the OS shutting us down
def shutdown(*args):
    door.shutdown()
    iface.close()

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


try:
    log.info("Let's go!")
    while True:
        sys.stdout.flush()
        time.sleep(1)
except KeyboardInterrupt:
    door.shutdown()
    iface.close()

# def on_position(packet, interface):
#     node = packet["fromId"]
#     pos = packet["decoded"]["position"]
#     lat = pos["latitude"]
#     lng = pos["longitude"]
#     alt = getattr(pos, "altitude", None)
#     log.info(f"position from {node}: {lat}, {lng} ({alt})")

#     if node not in POSITION_LOG:
#         POSITION_LOG[node] = []

#     POSITION_LOG[node].insert(0, (lat, lng))
#     clean_position_log()


# pub.subscribe(on_text, "meshtastic.receive.text")
# pub.subscribe(on_position, "meshtastic.receive.position")
