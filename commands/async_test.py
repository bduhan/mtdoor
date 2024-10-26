import time
import asyncio

from loguru import logger as log

from .base import BaseCommand

class AsyncTest(BaseCommand):
    command = "async"
    description = "test command"

    def invoke(self, msg: str, node: str) -> None:
        self.run_in_thread(self.wait_in_thread, msg, node)

    def wait_in_thread(self, msg, node):
        print(f"thread_method sleeping in response to '{msg}'..")
        time.sleep(5)
        print("thread_method done")
        self.send_dm("waited", node)


    # async def waiter(self, msg: str, node: str) -> None:
        
