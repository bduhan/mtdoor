from door.base_command import BaseCommand
from configparser import ConfigParser
from .mail_help import HelpManager
from .mail_db import initialize_database
from .mail_display import DisplayManager
from .mail_utils import (
    is_node_id,
    list_choices,
    make_node_list,
    get_longName,
    get_shortName,
    encode,
    decode,
)
from .mail_admin import admin
from loguru import logger as log
import base64
import zlib
import sqlite3
import re
from inspect import getmodule

class Mail(BaseCommand):
    command = "mail"
    description = "Exchange mail messages with other nodes"
    help = "'mail <read | delete | reply | send | admin>'"

    command_stack: dict[str, list[str]] = {}

    def load(self):
        self.helpmgr = HelpManager()
        self.command_stack = CommandStack()
        self.output = DisplayManager()
        admins = self.get_setting(str, "admins", "").replace(" ", "").split(",")
        self.profile = ProfileManager(admins)
        self.fmt = NodeDisplayFormat()

        # Make sure the node knows what time it is
        # We use lastHeard from the node list and
        # it returns invalid data if the time is
        # not set on the node
        self.interface.getNode("^local").setTime()

        # Initialize the database
        data_dir = self.get_setting(str, "data_dir", "./data")
        self.db = f"{data_dir}/mail.db"
        initialize_database(self.db)

    def invoke(self, msg: str, node: str) -> str:
        mailbox = self.profile.mailbox(node)

        log.debug(f"mailbox: {mailbox}")
        inp = InputHandler(msg)
        # Set up a persistent session so users
        # don't have to type 'mail' at the start
        # of every message
        if msg.strip().lower() == "exit":
            self.persistent_session(node, False)
            return "Mail: Goodbye"
        self.persistent_session(node, True)

        # Handle multi-page output controls
        if self.output.active(node):
            m = msg.strip().lower()
            # Clear search for display choices
            if m == "c":
                inp.pop()
            # Handle next, prev, and help for paged output
            if m in ["n", "p", "help"]:
                log.debug("User navigating display buffer")
                return self.output.display_pages(node, inp)
            # Toggle format settings for multi-page node lists
            if m in ["-", "+", "i", "l", "s"]:
                self.fmt.set(node, m)
                inp.pop()

        # Process user input
        # Mail commands / parmeters can be stacked
        # up in a single message, or entered
        # interactively one message at a time
        log.debug(f"inp:{inp.get_list()}")
        log.debug(f"command_stack:{self.command_stack.get(node, level=0)}")
        if not self.command_stack.get(node, level=0):
            self.command_stack.load(node, inp, ["mail"])

        if not self.command_stack.get(node, level=1):
            log.debug("No subcommand on stack")
            log.debug(f"inp:{inp.get_list()}")
            log.debug(f"command_stack:{self.command_stack.get(node)}")
            self.command_stack.load(
                node, inp, ["admin", "read", "reply", "send", "delete"]
            )

        log.debug(f"command_stack:{self.command_stack.get(node)}")
        log.debug(f"inp: {inp.get_list()}")
        if msg.strip().lower() in ["back", "up", "quit"] and self.command_stack.depth(node) > 1:
            log.debug("Processing '{msg.strip().lower()} subcommand")
            self.command_stack.pop(node)
            inp.pop()
        if self.command_stack.get(node, level=1) == "admin":
            log.debug("Processing '{self.command_stack.get(node, level=1)} subcommand")
            response = admin(self, node, inp)
        elif self.command_stack.get(node, level=1) == "read":
            log.debug("Processing '{self.command_stack.get(node, level=1)} subcommand")
            pass
        elif self.command_stack.get(node, level=1) == "reply":
            log.debug("Processing '{self.command_stack.get(node, level=1)} subcommand")
            pass
        elif self.command_stack.get(node, level=1) == "delete":
            log.debug("Processing '{self.command_stack.get(node, level=1)} subcommand")
            pass
        elif self.command_stack.get(node, level=1) == "send":
            log.debug("Processing '{self.command_stack.get(node, level=1)} subcommand")
            pass
        else:
            log.debug(
                "No valid subcommand to process: {self.command_stack.get(node, level=1)}"
            )
            response = self.helpmgr.get(self.command_stack.get(node), inp.get_list())
        if response is None:
            response = self.helpmgr.get(self.command_stack.get(node), inp.get_list())
        return self.output.display_pages(node, inp, text=response)


class NodeDisplayFormat:
    def __init__(self):
        self.fmt = {}

    def get(self, node):
        return self.fmt.get(node,"ils")

    def set(self, node, i):
        fmt = self.fmt.get(node,"ils")
        if i == "-":
            fmt = "s"    # Display only shortName
        elif i == "+":
            fmt = "ils"    # Display ID, longName, shorName
        elif i in "ils":
            if i in fmt:
                fmt = fmt.replace(i, "")
            else:
                fmt += i
        self.fmt[node] = fmt
        
class ProfileManager:
    def __init__(self, admins):
        self.profile = {}
        self.admins = admins
        log.debug(f"admins: {self.admins}")

    def is_admin(self, node):
        log.debug(f"admins: {self.admins}")
        return node in self.admins

    def mailbox(self, node):
        return self.profile.get(node, node)

    def select(self, node, mailbox):
        self.profile[node] = mailbox

    def clear(self):
        del self.profile[node]

class CommandStack:
    def __init__(self):
        self.stack = {}

    def push(self, node, value):
        if node not in self.stack:
            self.stack[node] = []
        self.stack[node].append(value)

    def pop(self, node):
        if node in self.stack and self.stack[node]:
            return self.stack[node].pop()
        return None

    def get(self, node, level=None):
        commands = self.stack.get(node, [])
        if level is None:
            return commands
        if 0 <= level < len(commands):
            return commands[level]
        else:
            return None

    def clear(self, node):
        if node in self.stack:
            self.stack[node] = ["mail"]

    def depth(self, node):
        return len(self.stack.get(node, []))

    def load(self, node, input_handler, valid_commands):
        """
        Load the first item from the input handler into the command stack
        if it matches one of the valid commands.
        """
        first_item = input_handler.get_current()
        if first_item in valid_commands:
            self.push(node, input_handler.pop())


class InputHandler:
    def __init__(self, msg=""):
        self.raw = msg
        self.arguments = msg.strip().split()

    def get_raw(self):
        return self.raw

    def get_list(self):
        return [arg.lower() for arg in self.arguments]

    def get_current(self):
        return self.arguments[0].lower() if self.arguments else ""

    def pop(self):
        if self.arguments:
            return self.arguments.pop(0).lower()
        return None
