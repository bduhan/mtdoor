# This file adds a command to the mtdoor node-bot.
# the 'mail' command allows users to send and receive
# emails with other nodes.
#
# Based on email feature from TC2BBS

from . import BaseCommand
from loguru import logger as log
import re
import sqlite3
import os
import time
from datetime import datetime, timedelta
import uuid
import pytz

class Mail(BaseCommand):
    command = "mail"
    description = "Send and receive mail messages from other nodes"
    help = "'mail' or\n"
    help += "'mail read [#]'\n"
    help += "'mail delete [#|all]'\n"
    help += "'mail send [!nodeID|shortName] [subject]'\n"
    help += "[parameters] are optional"

    def load(self):
        self.interface.getNode('^local').setTime()
        data_dir = self.get_setting(str, "data_dir", "./data")
        self.db = f"{data_dir}/mail.db"
        self.initialize_database()
        self.state = {}
        self.inputs = []



    def invoke(self, msg: str, node: str) -> str:
        if not self.state.get(node, None):
            self.state[node] = {
                "subcommand": "help",
                "list_index": 0,
                "to": None,
                "subject": None,
                "msg_content": False,
                "reply_to": None,
                "reply_subject": None,
            }

        # Retrieve the long name and ID of the local node
        my_node_info = self.interface.getMyNodeInfo()
        my_longName = my_node_info["user"]["longName"]
        my_shortName = my_node_info["user"]["shortName"]
        my_node_id = my_node_info["user"]["id"]

        # Set up a persistent session
        self.persistent_session(node, True)

        response = ""

        self.inputs = msg.strip().split()  # Parse incoming message
        inp = self.input()

        if self.state[node]["msg_content"] and msg.lower() == "exit":
            self.state[node]["msg_content"] = False
            self.state[node]["to"] = None
            self.state[node]["subject"] = None
            self.state[node]["reply_to"] = None
            self.state[node]["reply_subject"] = None
            self.state[node]["subcommand"] = "help"
            response += "Mail: send aborted\n"
        else:
            if inp == "exit":
                self.persistent_session(node, False)
                return "Exit mail, goodbye"
            if inp == "mail":
                inp = self.input(next=True)
            if inp in ["read", "reply", "send", "delete", "help"]:
                self.state[node]["subcommand"] = inp
                inp = self.input(next=True)

        if self.state[node]["subcommand"] in ["read", "delete"]:
            if inp in ["read", "delete"]:
                inp = self.input(next=True)
            messages = self.get_mail(node)
            if len(messages) == 0:
                response = "You have no mail messages waiting"
            elif inp.isdigit():
                index = int(inp) - 1
                if index < 0 or index >= len(messages):
                    return "Invalid choice"
                mail_id, sender_short_name, subject, date, unique_id = messages[index]
                if self.state[node]["subcommand"] == "read":
                    self.clear_notify(node, mail_id)
                    self.state[node]["reply_to"] = sender_short_name
                    self.state[node]["reply_subject"] = subject
                    message = self.get_mail_content(mail_id, node)
                    msg_text = f"{message[3]}"
                    header = f"From: {sender_short_name}\n"
                    header += f"Subject: {subject}\n"
                    header += f"Date: {date[5:]}\n\n"
                    header_length = len(header)
                    msg_length = len(msg_text)
                    # Drop header if message text is too long
                    if header_length + msg_length > 200:
                        response += msg_text
                    else:
                        response += f"{header}{msg_text}"
                    return response
                elif self.state[node]["subcommand"] == "delete":
                    self.delete_mail(unique_id, node)
                    self.state[node]["reply_to"] = None
                    self.state[node]["reply_subject"] = None
                    response = f"Deleted message #{index}\nFrom: {sender_short_name}\nSubject: {subject}\nDate: {date}"
            elif inp == "all" and self.state[node]["subcommand"] == "delete":
                self.state[node]["reply_to"] = None
                self.state[node]["reply_subject"] = None
                count = 0
                for index, message in enumerate(messages):
                    mail_id, sender_short_name, subject, date, unique_id = message
                    self.delete_mail(unique_id, node)
                    count += 1
                response = f"Deleted {count} messages"
            else:
                for index, message in enumerate(messages):
                    if inp == "m" and index <= self.state[node]["list_index"]:
                        continue
                    msg_id, sender_short_name, subject, date, unique_id = message
                    choice = f"{index + 1}) {sender_short_name} {subject} {date[5:]}\n"
                    if len(choice) + len(response) < 160:
                        response += choice
                        self.state[node]["list_index"] = index
                    else:
                        break
                if self.state[node]["subcommand"] == "delete":
                    response += "# or 'all' to select"
                else:
                    response += "# to select"

                if len(messages) - 1 > self.state[node]["list_index"]:
                    response += ", 'm' for more"
                response += ", 'exit' to quit"

        if self.state[node]["subcommand"] in ["send", "reply"]:

            if not self.state[node]["to"]:
                index = 0
                response = "To:\n"
                for node_id, n in self.interface.nodes.items():
                    index += 1
                    if (
                        (inp.isdigit() and int(inp) == index)
                        or (inp == node_id.lower())
                        or (inp == self.get_shortName(node_id).lower())
                        or (
                            self.state[node]["subcommand"] == "reply"
                            and self.state[node]["reply_to"]
                            == self.get_shortName(node_id)
                        )
                    ):
                        self.state[node]["to"] = node_id
                        inp = self.input(next=True)
                        response = ""
                        break
                    if inp == "m" and index <= self.state[node]["list_index"]:
                        continue
                    choice = f"{index}) {self.get_longName(node_id)} ({self.get_shortName(node_id)})\n"
                    if len(choice) + len(response) < 155:
                        response += choice
                        self.state[node]["list_index"] = index
                if not self.state[node]["to"]:
                    response += "# to select"
                    if (
                        len(self.interface.nodes.keys())
                        > self.state[node]["list_index"]
                    ):
                        response += ", 'm' for more"
                    response += ", 'exit' to quit"
                    return response

            if self.state[node]["to"] and not self.state[node]["subject"]:
                if (
                    self.state[node]["subcommand"] == "reply"
                    and self.state[node]["reply_subject"]
                ):
                    prefix = ""
                    if self.state[node]["reply_subject"][:4] != "re: ":
                        prefix = "re: "
                    self.state[node][
                        "subject"
                    ] = f"{prefix}{self.state[node]["reply_subject"]}"
                elif self.inputs:
                    self.state[node]["subject"] = " ".join(self.inputs)
                    self.inputs = []
                else:
                    self.state[node]["msg_content"] = True
                    recipient = self.state[node]["to"]
                    shortName = self.get_shortName(recipient)
                    longName = self.get_longName(recipient)
                    return f"Mail to: {recipient}\n{longName} ({shortName})\nEnter subject:"

            if self.state[node]["to"] and self.state[node]["subject"]:
                recipient = self.state[node]["to"]
                r_shortName = self.get_shortName(recipient)
                r_longName = self.get_longName(recipient)
                s_shortName = self.get_shortName(node)
                s_longName = self.get_longName(node)
                subject = self.state[node]["subject"]
                if self.inputs:
                    msg_text = " ".join(self.inputs)[:200]
                    self.add_mail(
                        node,
                        s_shortName,
                        recipient,
                        subject,
                        msg_text,
                    )
                    response = "Sent message\n"
                    response += f"From: {node}\n"
                    response += f"To: {recipient}\n"
                    response += f"Subject: {subject}\n\n"
                    header_length = len(response)
                    msg_length = len(msg_text)
                    if header_length + msg_length > 200:
                        l = 200 - msg_length - 3
                        response += f"{msg_text[:l]}..."
                    else:
                        response += msg_text
                    return response

                    self.state[node]["msg_content"] = False
                    self.state[node]["to"] = None
                    self.state[node]["subject"] = None
                    self.state[node]["reply_to"] = None
                    self.state[node]["reply_subject"] = None
                    self.state[node]["subcommand"] = "help"
                else:
                    self.state[node]["msg_content"] = True
                    return f"Mail to: {recipient}\n{r_longName} ({r_shortName})\nSubject: {subject}\nEnter message text:"

        if self.state[node]["subcommand"] == "help":
            response += f"You have {len(self.get_mail(node))} messages\n"
            response += "Mail: 'read', 'reply', 'send', 'delete', or 'exit' to quit"

        return response[:200]

    def periodic(self):
        # Check to see if we have heard from any nodes recently
        # who have new mail messages waiting

        self.local_tz = pytz.timezone("America/Chicago")
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            "SELECT recipient, id FROM mail WHERE id IN (SELECT MAX(id) "
            "FROM mail WHERE notify = 1 GROUP BY recipient);"
        )
        for recipient, mail_id in c.fetchall():
            log.debug(f"recipient: {recipient} mail_id: {mail_id}")
            node = self.interface.nodes.get(recipient, None)
            if node:
                lastHeard = node.get("lastHeard", None)
                if lastHeard is None:
                    continue
                lh = f"{datetime.fromtimestamp(lastHeard, self.local_tz).strftime('%Y-%m-%d %H:%M:%S')}"
                log.debug(f"{datetime.now() - datetime.fromtimestamp(lastHeard)} ago")
                if datetime.now() - datetime.fromtimestamp(lastHeard) < timedelta(
                    seconds=300
                ):
                    log.debug(f"Node {recipient} heard recently, notifying of new mail")
                    message = "You have new mail messages. Reply with 'mail' to see them."
                    self.send_dm(message, recipient)
                    self.clear_notify(recipient, mail_id)

    def clear_notify(self, recipient, mail_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            f"UPDATE mail SET notify = 0 WHERE recipient = ? AND id <= ? AND notify = 1;",
            (recipient, mail_id)
        )
        conn.commit()

    def get_longName(self, node_id):
        fallback = f"Meshtastic_{node_id[-4:]}"
        node = self.interface.nodes.get(node_id, None)
        if node and node.get("user", None):
            return node["user"].get("longName", fallback)
        else:
            return fallback

    def get_shortName(self, node_id):
        fallback = node_id[-4:]
        node = self.interface.nodes.get(node_id, None)
        if node and node.get("user", None):
            return node["user"].get("shortName", fallback)
        else:
            return fallback

    def input(self, next=False):
        if next and self.inputs:
            del self.inputs[0]
        return self.inputs[0].lower() if self.inputs else ""

    def get_db_connection(self):
        return sqlite3.connect(self.db)

    def initialize_database(self):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS mail (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        sender_short_name TEXT NOT NULL,
                        recipient TEXT NOT NULL,
                        date TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        content TEXT NOT NULL,
                        unique_id TEXT NOT NULL,
                        notify BOOLEAN DEFAULT 1
                    );"""
        )
        conn.commit()

    def add_mail(
        self,
        sender_id,
        sender_short_name,
        recipient_id,
        subject,
        content,
        unique_id=None,
    ):
        conn = self.get_db_connection()
        c = conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        if not unique_id:
            unique_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO mail (sender, sender_short_name, recipient, date, subject, content, unique_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                sender_id,
                sender_short_name,
                recipient_id,
                date,
                subject,
                content,
                unique_id,
            ),
        )
        conn.commit()
        # TODO - Make this interoperable with Tc2-BBS
        # if self.bbs_nodes and self.interface:
        #    send_mail_to_bbs_nodes(sender_id, sender_short_name, recipient_id, subject, content, unique_id, bbs_nodes, interface)
        return unique_id

    def get_mail(self, recipient_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            "SELECT id, sender_short_name, subject, date, unique_id FROM mail WHERE recipient = ?",
            (recipient_id,),
        )
        return c.fetchall()

    def get_mail_content(self, mail_id, recipient_id):
        # TODO: ensure only recipient can read mail
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            "SELECT sender_short_name, date, subject, content, unique_id FROM mail WHERE id = ? and recipient = ?",
            (
                mail_id,
                recipient_id,
            ),
        )
        return c.fetchone()

    def delete_mail(self, unique_id, recipient_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT recipient FROM mail WHERE unique_id = ?", (unique_id,))
            result = c.fetchone()
            if result is None:
                log.error(f"No mail found with unique_id: {unique_id}")
                return  # Early exit if no matching mail found
            recipient_id = result[0]
            log.info(
                f"Attempting to delete mail with unique_id: {unique_id} by {recipient_id}"
            )
            c.execute(
                "DELETE FROM mail WHERE unique_id = ? and recipient = ?",
                (
                    unique_id,
                    recipient_id,
                ),
            )
            conn.commit()
            # TODO - Make this interoperable with Tc2-BBS
            # send_delete_mail_to_bbs_nodes(unique_id, bbs_nodes, interface)
            log.info(f"Mail with unique_id: {unique_id} deleted and sync message sent.")
        except Exception as e:
            log.error(f"Error deleting mail with unique_id {unique_id}: {e}")
            raise

    def get_sender_id_by_mail_id(self, mail_id):
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT sender FROM mail WHERE id = ?", (mail_id,))
        result = c.fetchone()
        if result:
            return result[0]
        return None
