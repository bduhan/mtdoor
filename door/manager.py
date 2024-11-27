from configparser import ConfigParser
from inspect import getmodule
from meshtastic.mesh_interface import MeshInterface
from loguru import logger as log
from pubsub import pub
from .base_command import (
    BaseCommand,
    CommandLoadError,
    CommandRunError,
    CommandActionNotImplemented,
)
import inspect


class DoorManager:
    # use this topic to send response messages
    dm_topic: str = "mtdoor.send.text"

    def __init__(self, interface: MeshInterface, settings: ConfigParser):
        self.interface = interface
        self.settings = settings
        self.me = interface.getMyUser()["id"]
        self.default_command = dict(self.settings.items("global")).get(
            "default_command", "help"
        )
        self.previous_command = {}  # save command name here for persistent sessions

        # keep track of the commands added, don't let duplicates happen
        self.commands = []

        pub.subscribe(self.on_text, "meshtastic.receive.text")
        pub.subscribe(self.send_dm, self.dm_topic)

        log.info(f"DoorManager is connected to {self.me}")

    def add_command(self, command: BaseCommand):
        if not hasattr(command, "command"):
            raise CommandLoadError("No 'command' property on {command}")

        cmd: BaseCommand
        for cmd in self.commands:
            if cmd.command == command.command:
                raise CommandLoadError("Command already loaded")

        # instantiate and set some properties
        cmd = command()
        module = getmodule(cmd).__name__

        # commands can publish responses with this topic
        cmd.dm_topic = self.dm_topic

        # commands can access the Meshtastic interface
        cmd.interface = self.interface

        # commands can access the ConfigParser settings file
        cmd.settings = self.settings

        # call "load" on the command class
        try:
            log.debug(f"Loading '{cmd.command}' command from '{module}'..")
            cmd.load()
        except CommandActionNotImplemented:
            # it's ok if they don't implement a load method
            pass
        except CommandLoadError:
            log.warning(f"Command {command.command} could not load.")
            return
        except:
            log.exception(f"Failed to load {command.command}")
            return

        self.commands.append(cmd)

    def add_commands(self, commands: list[BaseCommand]):
        for cmd in commands:
            self.add_command(cmd)

    def get_command_handler(self, message: str):
        cmd: BaseCommand
        for cmd in self.commands:
            if len(message) >= len(cmd.command):
                if message[: len(cmd.command)] == cmd.command:
                    return cmd
        return None

    def send_dm(self, message: str, node: str):
        """
        break up the rx -> tx loop so maybe other messages can get through
        """
        if type(message) != type(""):
            log.warning("Skipping attempt to send {node} non-string: {message}")
            return
        log.info(f"TX {node} ({len(message):>3}): {message}")
        self.interface.sendText(message, node)

    def help_message(self):
        invoke_list = ", ".join([cmd.command for cmd in self.commands])
        return f"Hi, I am a bot.\n\nTry one of these commands: {invoke_list} or 'help <command>'."

    def help_command(self, command: BaseCommand) -> str:
        """build a help message for the given command
        we may or may not have 'description' or 'help' filled in
        """
        description = getattr(command, "description", None)
        help = getattr(command, "help", None)
        if description and help:
            return description + "\n\n" + help
        elif description and not help:
            return description
        elif not description and help:
            return help
        else:
            return "No help for this command"

    def on_text(self, packet, interface):
        # ignore messages not directed to the connected node
        if packet["toId"] != self.me:
            return

        node = packet["fromId"]
        msg: str = packet["decoded"]["payload"].decode("utf-8")
        response = None
        command = msg.lower().split()[0]

        log.info(f"RX {node} ({len(msg):>3}): {msg}")

        # skip if responses are disabled globally
        if self.settings.getboolean("global", "disable_all_responses", fallback=False):
            log.debug("Not responding.")
            return

        # Check for ongoing session with previous command
        # If we have a persistent session, the user does not have to
        # keep typing the command at the beginning of every msg
        if self.previous_command.get(node, False):
            # We found the previous command from this node
            # Let's check the session state in the command handler
            handler = self.get_command_handler(self.previous_command[node])
            if handler:
                # Handler found, check for persistent session
                if handler.persistent_session(node):
                    try:
                        response = handler.invoke(msg, node)
                    except CommandRunError:
                        response = f"Command to '{handler.command}' failed."
                else:
                    # No persistent session. Remember the current command
                    self.previous_command[node] = command
            else:
                # No handler for previous command. Remember the current command
                self.previous_command[node] = command
        else:
            # No previous command for this node. Remember this command for later
            self.previous_command[node] = command

        if response:
            # Got response from persistent session. Send it!
            pub.sendMessage(self.dm_topic, message=response, node=node)
            return

        # show help for commands
        if msg.lower()[:5] == "help ":
            handler = self.get_command_handler(msg[5:].lower())
            if handler:
                pub.sendMessage(
                    self.dm_topic, message=self.help_command(handler), node=node
                )
                return

        # show global help
        if msg.lower()[:4] == "help":
            pub.sendMessage(self.dm_topic, message=self.help_message(), node=node)
            return

        # look for a regular command handler
        handler = self.get_command_handler(msg.lower())
        if handler:
            try:
                if "packet" in inspect.signature(handler.invoke).parameters.keys():
                    # Expose packet data to commands like 'ping'
                    response = handler.invoke(msg, node, packet=packet)
                else:
                    response = handler.invoke(msg, node)
            except CommandRunError:
                response = f"Command to '{handler.command}' failed."
        else:
            # Attempt to load the default handler
            handler = self.get_command_handler(self.default_command)
            if handler:
                try:
                    response = handler.invoke(f"{self.default_command} {msg}", node)
                except CommandRunError:
                    response = f"Command to '{handler.command}' failed."
            else:
                # No default handler available. Show help message
                response = self.help_message()

        # command handlers may or may not return a response
        # they have the option of handling it themselves on long-running tasks
        # by calling CommandBase.send_dm
        if response:
            pub.sendMessage(self.dm_topic, message=response, node=node)

    def periodic(self):
        log.debug("Calling .periodic() on every command..")
        for command in self.commands:
            try:
                command.periodic()
            except CommandActionNotImplemented:
                pass
            except:
                log.exception(f"{command.__name__}.periodic failed")

    def shutdown(self):
        log.debug(f"Shutting down {len(self.commands)} commands..")
        command: BaseCommand
        for command in self.commands:
            try:
                command.shutdown()
            except CommandActionNotImplemented:
                pass
