import threading

from loguru import logger as log
from ...base_command import BaseCommand

from .app import run


class RestAPI(BaseCommand):
    """
    Start FastAPI with access to the meshtastic interface in a thread
    """

    command = "api"

    def load(self):
        self.host = self.get_setting(str, "http_host", "127.0.0.1")
        self.port = self.get_setting(int, "http_port", 8989)
        self.api_key = self.get_setting(str, "api_key", None)

        log.debug(f"Starting rest_api service on {self.host}:{self.port} with api_key: {self.api_key}")
        thread = threading.Thread(
            name="REST API", target=run, args=(self.interface, self.host, self.port, self.api_key)
        )
        thread.run()

    def invoke(self, msg: str, node: str):
        msg = f"REST API is running on {self.host}:{self.port}."
        if self.api_key:
            msg += " An API key is configured."
        return msg
