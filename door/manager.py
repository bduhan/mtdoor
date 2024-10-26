from meshtastic.mesh_interface import MeshInterface
from loguru import logger as log
from pubsub import pub

from .commands import (
    BaseCommand,
    CommandLoadError,
    CommandRunError,
    CommandActionNotImplemented,
)


class DoorManager:
    # use this topic to send response messages
    dm_topic: str = "mtdoor.send.text"

    def __init__(self, interface: MeshInterface):
        self.interface = interface
        self.me = interface.getMyUser()["id"]

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
        cmd.dm_topic = self.dm_topic
        cmd.interface = self.interface

        # call "load" on the command class
        try:
            log.debug(f"Loading '{cmd.command}'..")
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
        if command.description and command.help:
            return command.description + "\n\n" + command.help
        elif command.description and not command.help:
            return command.description
        elif not command.description and command.help:
            return command.help
        else:
            return "No help for this command"

    def on_text(self, packet, interface):
        # ignore messages not directed to the connected node
        if packet["toId"] != self.me:
            return

        node = packet["fromId"]
        msg: str = packet["decoded"]["payload"].decode("utf-8")
        response = None

        log.info(f"RX {node} ({len(msg):>3}): {msg}")

        # show help for commands
        if msg.lower()[:5] == "help ":
            handler = self.get_command_handler(msg[5:].lower())
            if handler:
                pub.sendMessage(
                    self.dm_topic, message=self.help_command(handler), node=node
                )
                return

        # look for a regular command handler
        handler = self.get_command_handler(msg.lower())
        if handler:
            try:
                response = handler.invoke(msg, node)
            except CommandRunError:
                response = f"Command to '{handler.command}' failed."
        else:
            response = self.help_message()

        # command handlers may or may not return a response
        # they have the option of handling it themselves on long-running tasks
        # by calling CommandBase.send_dm
        if response:
            pub.sendMessage(self.dm_topic, message=response, node=node)

    def shutdown(self):
        log.debug(f"Shutting down {len(self.commands)} commands..")
        command: BaseCommand
        for command in self.commands:
            try:
                command.shutdown()
            except CommandActionNotImplemented:
                pass
