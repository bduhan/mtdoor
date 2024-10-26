import subprocess
from shutil import which

from loguru import logger as log

from .base_command import BaseCommand, CommandRunError, CommandLoadError

class Fortune(BaseCommand):
    command = "fortune"
    description = "open a fortune cookie"
    help = "Run the *nix 'fortune' command with -a and -s options."

    def load(self):
        self.fortune = which("fortune")

        if self.fortune is None:
            log.exception("'fortune' is not available in your environment")
            raise CommandLoadError("'fortune' not found in path")
    
    def invoke(self, msg: str, node: str) -> str:
        try:
            response = subprocess.run(
                [self.fortune, "-a", "-s"], capture_output=True, text=True, check=True
            )
            fortune = response.stdout.strip()
        except:
            fortune = "'fortune' command failed"
            log.exception(fortune)
            raise CommandRunError(fortune)
        return fortune
