import time
import asyncio

from rich.pretty import pprint

from loguru import logger as log

from .base_command import BaseCommand

class AsyncTest(BaseCommand):
    command = "async"
    description = "test command"

    def invoke(self, msg: str, node: str) -> None:
        self.run_in_thread(self.wait_in_thread, msg, node)

    def wait_in_thread(self, msg, node):
        print(f"thread_method sleeping in response to '{msg}'..")
        pprint(self.get_node(node))
        time.sleep(5)
        print("thread_method done")
        self.send_dm("waited", node)


    # async def waiter(self, msg: str, node: str) -> None:
        
