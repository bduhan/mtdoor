from loguru import logger as log

# shortcut for imports
from .base import BaseCommand, CommandLoadError, CommandRunError, CommandActionNotImplemented

# TODO move this to the main script? eventually we want some degree of configurability
from .ping import Ping
from .fortune import Fortune
from .weather import Weather
from .rss import RSS
from .async_test import AsyncTest
from .llm import ChatGPT
from .astro import Astro

all_commands = [Ping, Fortune, RSS, Weather, AsyncTest, ChatGPT, Astro]

def load_commands(dm_topic: str) -> list[BaseCommand]:
    """
    create each command and try to call '.load()' on it
    """
    results = []
    for command in all_commands:
        cmd = command()
        command.dm_topic = dm_topic

        if not hasattr(cmd, "command"):
            log.warning(f"{command} 'command' attribute is required")
            continue

        # call "load" on the command class
        try:
            log.debug(f"Loading '{cmd.command}'..")
            cmd.load()
        except CommandActionNotImplemented:
            # it's ok if they don't implement a load method
            pass
        except CommandLoadError:
            log.warning(f"Command {command.command} could not load.")
            continue
        except:
            log.exception(f"Failed to load {command.command}")
            continue
        results.append(cmd)
    return results
