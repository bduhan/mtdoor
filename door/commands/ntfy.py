# This file adds a command to the mtdoor node-bot.
# The 'msg' command will send a message to the 
# node operator using NTFY. This is intended to make
# it possible for users to contact the owner of
# a node that is not actively monitored.

# Include the following lines in config.ini
# [door.commands.msg]
# enabled = true
# ntfy_url = https://ntfy.mydomain.com/meshtastic
# ntfy_user = meshtastic
# ntfy_token = my-ntfy-user-token

import requests
import time
from loguru import logger as log
from . import BaseCommand

class Ntfy(BaseCommand):
    """
    Send message to node operator
    """
    command = "msg"
    description = "Send message to the node operator"
    help = "msg Hello node operator!"

    def load(self):
        self.ntfy_url = self.get_setting(str, "ntfy_url", None) 
        self.username = self.get_setting(str, "ntfy_user", None)
        self.access_token = self.get_setting(str, "ntfy_token", None)
        if not (self.ntfy_url and self.username and self.access_token):
            log.exception("Failed to load Ntfy. Check settings in config.ini")
            raise CommandLoadError()

    def invoke(self, msg: str, node: str) -> str:
        """Send the message text to the ntfy server with authentication and return a confirmation."""

        # Retrieve the long name and ID of the local node
        local_node_info = self.interface.getMyNodeInfo()
        local_node_long_name = local_node_info['user']['longName']
        local_node_short_name = local_node_info['user']['shortName']
        local_node_id = local_node_info['user']['id']
    
        # Retrieve the long name of the sending node
        sender_info = self.interface.nodes.get(node)
        sender_long_name = sender_info['user']['longName'] if sender_info else "Unknown Sender"
        sender_short_name = sender_info['user']['shortName'] if sender_info else "node"


        full_message = (f"From: {sender_long_name} ({sender_short_name})\n"
                        f"To: {local_node_long_name} ({local_node_short_name})\n"
                        f"{msg[len('msg '):].strip()}")
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.post(self.ntfy_url, data=full_message, headers=headers)
            response.raise_for_status()
            return "Message sent to the operator via ntfy."
        except requests.RequestException as e:
            return f"Failed to send message to ntfy server: {e}"

