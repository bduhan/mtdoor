import sys, time, signal, argparse, configparser
from pathlib import Path

from loguru import logger as log
from meshtastic.serial_interface import SerialInterface
from pubsub import pub

from door.manager import DoorManager
from door.config import find_commands


# parse arguments
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description="Meshtastic Door Bot",
)
parser.add_argument("config_file", type=Path, help=".ini file")
parser.add_argument("--serial", type=str, default=None, help="Serial device of node.")
# TODO make logs configurable

args = parser.parse_args()


# read settings
settings = configparser.ConfigParser()
try:
    assert args.config_file.exists()
    settings.read(args.config_file)
except:
    log.exception(f"Failed to read config_file '{args.config_file}")
    sys.exit(1)


# some commands need a place to write data
data_dir = settings.get("global", "data_dir", fallback=None)
if not data_dir:
    data_dir = Path().cwd() / "data"
    settings.set("global", "data_dir", str(data_dir))
else:
    data_dir = Path(data_dir)

try:
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
except:
    log.error(f"Failed to create '{data_dir}'.")


# find plugins
available_commands = find_commands(settings)
log.debug(
    f"Found {len(available_commands)} available commands: {[c.__name__ for c in available_commands]}"
)


# create door manager
door: DoorManager
should_shut_down = False


def connected(interface, **kwargs):
    global door
    door = DoorManager(interface, settings)
    door.add_commands(available_commands)


# handle the OS shutting us down
def shutdown(*args, **kwargs):
    door.shutdown()
    interface.close()
    time.sleep(0.5)
    sys.exit(0)


def shutting_down(interface):
    global should_shut_down
    should_shut_down = True
    log.debug("Device connection lost.")


# TODO support BLE and TCP interfaces
interface = SerialInterface(args.serial)
log.info("Waiting on Meshtastic device connection..")

pub.subscribe(connected, "meshtastic.connection.established")
pub.subscribe(shutting_down, "meshtastic.connection.lost")

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


# if configured, call DoorManager.periodic regularly
periodic_wait = settings.getint("global", "periodic_call_seconds", fallback=0)
last_periodic = time.time()

# main loop
try:
    while should_shut_down != True:
        sys.stdout.flush()
        time.sleep(1)

        # check if it's time to run periodic tasks
        now = int(time.time())
        if periodic_wait > 0 and now - last_periodic > periodic_wait:
            door.periodic()
            last_periodic = now

except KeyboardInterrupt:
    pass

shutdown()
