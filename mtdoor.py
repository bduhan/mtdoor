import sys, time, signal

from loguru import logger as log
from meshtastic.serial_interface import SerialInterface

from door.manager import DoorManager
from door.commands import all_commands


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
