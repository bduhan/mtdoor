from . import BaseCommand


class Ping(BaseCommand):
    command = "ping"
    description = "'ping' replies with 'pong'"
    help = "This could be useful to test connectivity."

    def invoke(self, msg: str, node: str) -> str:
        return "pong"
