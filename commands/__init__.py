
# shortcuts for imports
from .base import BaseCommand, CommandLoadError, CommandRunError, CommandActionNotImplemented

# command handlers
from .ping import Ping
from .fortune import Fortune
from .weather import Weather
from .rss import RSS
from .async_test import AsyncTest
from .llm import ChatGPT
from .astro import Astro

all_commands = [Ping, Fortune, RSS, Weather, AsyncTest, ChatGPT, Astro]
