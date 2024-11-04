"""
Example command. Must be in an accessible Python module path.

Activate in mtdoor.py configuration by adding:

[example_command]

"""

from door.base_command import BaseCommand

class Command(BaseCommand):
    command = "example"

    def invoke(self, message: str, node: str) -> str:
        return "hello, world"