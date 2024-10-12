import sys, time, subprocess

import requests
from loguru import logger as log
import meshtastic
from meshtastic.serial_interface import SerialInterface

from pubsub import pub

from sky import solar_position, moon_phase
from gpt import ChatGPT

## services ##


def ping(msg: str, node: int) -> str:
    return "pong"


def about(msg: str, node: int) -> str:
    # return """I made this for fun one Saturday in October."""
    return "*" * 201


def fortune(msg: str, node: int) -> str:
    try:
        response = subprocess.run(
            ["fortune", "-a", "-s"], capture_output=True, text=True, check=True
        )
        fortune = response.stdout.strip()
        return fortune
    except:
        log.exception(f"'fortune' command failed")
        return


def forecast(msg: str, node: int) -> str:
    # Lubbock County
    request = requests.get("https://api.weather.gov/zones/county/TXZ035/forecast")
    request.raise_for_status()
    data = request.json()
    forecast = data["properties"]["periods"]

    # return the first periods that fit in our message size

    response = ""

    for p in forecast:
        proposed_addition = f"({p['name']}) {p['detailedForecast']}\n"
        if len(response + proposed_addition) > 200:
            break
        else:
            response += proposed_addition

    return response.strip()


POSITION_LOG: dict[list] = {}  # key is node, value is list of last positions
POSITION_LOG_SIZE = 5


def clean_position_log():
    "only keep the most recent entries (newest first)"
    for node, logs in POSITION_LOG.items():
        if len(logs) > POSITION_LOG_SIZE:
            POSITION_LOG[node] = logs[:POSITION_LOG_SIZE]


def position_log(msg: str, node: int) -> str:
    if node not in POSITION_LOG:
        return "No positions found. Share one with me."
    response = "Last positions: (newest first)\n"

    for lat, lng in POSITION_LOG[node]:
        response += f"{lat}, {lng}\n"

    return response


def get_sun_position(msg: str, node: int) -> str:
    altitude, azimuth = solar_position()
    return f"🌞 altitude: {altitude}°, azimuth: {azimuth}°"


def get_moon_phase(msg: str, node: int) -> str:
    response = f"👾 DA MOON RULEZ #1 👾\n\n{moon_phase()}"
    return response


gpt = ChatGPT()


def chat_gpt(msg: str, node: int) -> str:
    msg = msg[4:]
    response = gpt.chat(node, msg)
    return response


## commands ##

commands = [
    # ("about", "not much info", about),
    ("ping", "pong", ping),
    ("fortune", "crack open a cookie", fortune),
    ("forecast", "LBK county", forecast),
    ("positions", f"last {POSITION_LOG_SIZE} you sent", position_log),
    ("sun", "position of the sun", get_sun_position),
    ("moon", "phase of the moon", get_moon_phase),
    ("gpt", "'gpt <query>' to ask the oracle", chat_gpt),
]


def help_message() -> str:
    msg = "- commands -\n" + "\n".join(
        [f"{cmd}: { desc }" for (cmd, desc, handler) in commands]
    )
    return msg


def get_command_handler(msg: str):
    for cmd, desc, handler in commands:
        if len(msg) >= len(cmd):
            if msg[: len(cmd)] == cmd:
                return handler
    return None


## incoming mesh messages ##


def on_text(packet, interface):
    node = packet["fromId"]
    msg: str = packet["decoded"]["payload"].decode("utf-8")

    log.info(f"{node} (rx): {msg}")

    handler = get_command_handler(msg.lower())

    if handler is None:
        response = help_message()
    else:
        response = handler(msg.lower(), node)

    log.info(f"{node} (tx {len(response):>3}): {response}")
    interface.sendText(response, node)


def on_position(packet, interface):
    node = packet["fromId"]
    pos = packet["decoded"]["position"]
    lat = pos["latitude"]
    lng = pos["longitude"]
    alt = getattr(pos, "altitude", None)
    log.info(f"position from {node}: {lat}, {lng} ({alt})")

    if node not in POSITION_LOG:
        POSITION_LOG[node] = []

    POSITION_LOG[node].insert(0, (lat, lng))
    clean_position_log()


if __name__ == "__main__":
    # opening the interface and looping forever allows pubsub messages from the radio
    # to start
    iface = SerialInterface()
    pub.subscribe(on_text, "meshtastic.receive.text")
    pub.subscribe(on_position, "meshtastic.receive.position")

    try:
        log.info("Let's go!")
        while True:
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Bye")
        iface.close()
