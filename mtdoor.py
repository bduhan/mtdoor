import sys, time, signal, argparse, configparser
from pathlib import Path

from loguru import logger as log
from meshtastic.serial_interface import SerialInterface

from door.manager import DoorManager
from door.config import find_commands

# parse arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description="Meshtastic Door Bot")
parser.add_argument("config_file", type=Path, help=".ini file")
parser.add_argument("--serial", type=str, default=None, help="Path to serial device.")
# TODO make logs configurable

args = parser.parse_args()
# log.debug(args)

# read settings
settings = configparser.ConfigParser()
try:
    assert args.config_file.exists()
    settings.read(args.config_file)
    # log.debug(dict(settings))
except:
    log.exception(f"Failed to read config_file '{args.config_file}")
    sys.exit(1)

# find plugins
available_commands = find_commands(settings)
log.debug(f"Found {len(available_commands)} available commands: {[c.__name__ for c in available_commands]}")


# create door manager
# TODO support BLE and TCP interfaces
interface = SerialInterface(args.serial)
door = DoorManager(interface, settings)

door.add_commands(available_commands)

#sys.exit(1)


# handle the OS shutting us down
def shutdown(*args):
    door.shutdown()
    interface.close()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


try:
    log.info("Let's go!")
    while True:
        sys.stdout.flush()
        time.sleep(1)
except KeyboardInterrupt:
    door.shutdown()
    interface.close()
