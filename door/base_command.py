import threading
from inspect import getmodule
from collections.abc import Callable
from configparser import ConfigParser
from pathlib import Path

from meshtastic.mesh_interface import MeshInterface

from loguru import logger as log
from pubsub import pub

from .models import NodeInfo


class CommandRunError(Exception):
    pass


class CommandLoadError(Exception):
    pass


class CommandActionNotImplemented(Exception):
    pass


class BaseCommand:
    """
    to make a custom command, extend this class, set properties, and implement functions

    when invoke(..) has a response, call self.send_response and the DoorManager
    will dispatch a message to Meshtastic
    """

    # incoming messages with this string will be passed to invoke(..)
    command: str

    # displayed in commands list
    description: str

    # displayed when 'help <command>' is called
    help: str

    # pubsub topic handlers send responses to - set by DoorManager
    dm_topic: str

    # Meshtastic interface
    interface: MeshInterface

    # global settings object
    settings: ConfigParser

    def load(self):
        """
        raise CommandLoadError if we don't have resources necessary to operate
        """
        raise CommandActionNotImplemented()

    def periodic(self):
        """
        called by main program every global.periodic_call_seconds
        """
        raise CommandActionNotImplemented()

    def shutdown(self):
        raise CommandActionNotImplemented()

    def invoke(self, message: str, node: str) -> str:
        raise CommandActionNotImplemented()

    def send_dm(self, message: str, node: str) -> str:
        """
        when command has a response for a node, call this
        """
        pub.sendMessage(self.dm_topic, message=message, node=node)

    def run_in_thread(
        self, method: Callable[[str, str], None], message: str, node: str
    ) -> None:
        """
        allow command handlers to start a thread then use send_dm to return a response at some later time
        method takes positional arguments (message, node)
        """
        thread = threading.Thread(
            target=method, args=(message, node), name=self.command
        )
        thread.start()

    def get_node(self, node: str) -> NodeInfo:
        """
        try to fetch the detailed node information in meshtastic.interface[node]
        """
        if node in self.interface.nodes:
            return NodeInfo(**self.interface.nodes[node])

    def get_setting(self, type, name: str, default=None):
        """
        fetch setting from the 'global' or module path section of the config file
        """
        module = getmodule(self).__name__

        # In case command is in a subdirectory
        if module not in self.settings.sections():
            module = module.rsplit('.', 1)[0]

        # where should we get this setting from?
        source = None
        if self.settings.has_option(module, name):
            source = module
        elif self.settings.has_option("global", name):
            source = "global"
        else:
            return default

        # type the result
        if type == int:
            return self.settings.getint(source, name, fallback=default)
        elif type == float:
            return self.settings.getfloat(source, name, fallback=default)
        elif type == bool:
            return self.settings.getboolean(source, name, fallback=default)
        elif type == Path:
            return Path(self.settings.get(source, name, fallback=default))
        else:
            return self.settings.get(source, name, fallback=default)
