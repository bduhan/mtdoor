import time

from loguru import logger as log

from . import BaseCommand


class AsyncTest(BaseCommand):
    """
    Demonstrates a background thread.
    """
    command = "async"
    description = "test command"
    help = "Run a thread, sleep for some seconds, reply."

    delay: int = 5

    def load(self):
        self.delay = self.get_setting(int, "delay", 8)

    def invoke(self, msg: str, node: str) -> None:
        self.run_in_thread(self.wait_in_thread, msg, node)

    def wait_in_thread(self, msg, node):
        log.debug(self.get_node(node))
        log.debug(f"thread_method sleeping..")
        time.sleep(self.delay)
        log.debug("thread_method done")
        self.send_dm(f"waited {self.delay} seconds", node)
