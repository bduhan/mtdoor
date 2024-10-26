import time

from loguru import logger as log

from .base_command import BaseCommand


class AsyncTest(BaseCommand):
    """
    Demonstrates a background thread.
    """
    command = "async"
    description = "test command"
    help = "Run a thread, sleep for 10 seconds, reply."

    def invoke(self, msg: str, node: str) -> None:
        self.run_in_thread(self.wait_in_thread, msg, node)

    def wait_in_thread(self, msg, node):
        log.debug(self.get_node(node))
        log.debug(f"thread_method sleeping..")
        time.sleep(10)
        log.debug("thread_method done")
        self.send_dm("waited", node)
