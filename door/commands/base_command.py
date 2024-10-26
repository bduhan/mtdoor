import threading
from meshtastic.mesh_interface import MeshInterface
from collections.abc import Callable

from loguru import logger as log
from pubsub import pub


from ..models import Node

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

    def load(self):
        """
        raise CommandLoadError if we don't have resources necessary to operate
        """
        raise CommandActionNotImplemented()

    def clean(self):
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
    
    def run_in_thread(self, method: Callable[[str, str], None], message: str, node: str) -> None:
        """
        allow command handlers to start a thread then use send_dm to return a response at some later time
        method takes positional arguments (message, node)
        """
        thread = threading.Thread(target=method, args=(message, node))
        log.debug("thread.start")
        thread.start()
    
    def get_node(self, node: str) -> Node:
        """
        try to fetch the detailed node information in meshtastic.interface[node]
        """
        if node in self.interface.nodes:
            return Node(**self.interface.nodes[node])
