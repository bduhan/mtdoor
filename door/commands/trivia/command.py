"""
questions from https://github.com/uberspot/OpenTriviaQA/
"""

from pathlib import Path
import threading
import sqlite3

from loguru import logger as log

from .. import BaseCommand
from .data import load_database
from .game import TriviaGame


class TriviaCommand(BaseCommand):
    """
    idea:
    'trivia' asks a new question (and skips the last)
    'trivia last' restates the last question (if present), or returns a new one
    'trivia stats' shows count of correct/incorrect
    'trivia clear' clears all responses
    'trivia categories' shows a list of categories

    to start, just ask and get response
    """

    command = "trivia"
    description = "answer trivia questions"
    help = "Commands: 'skip', 'clear', 'last', 'stats'.\n\nAnswer questions with 'a', 'b', 'c', or 'd'."

    def __init__(self):
        # acquire lock before writing to the database
        self.lock = threading.Lock()

    def load(self):
        self.db_file = Path(__file__).parent.parent / "data" / "trivia.sqlite"

        # TODO move this to configuration ?
        questions_path = (
            Path(__file__).parent.parent.parent.parent / "OpenTriviaQA" / "categories"
        )
        load_database(self.db_file, questions_path)

    def invoke(self, msg: str, node: str):
        self.run_in_thread(self.play, msg, node)

    def play(self, msg: str, node: str):
        """
        'trivia' asks a new question
        'trivia <answer>' checks your answer
        """

        msg = msg[len(self.command) :].lower().lstrip().rstrip()
        response = None

        with self.lock:
            db = sqlite3.connect()
            cursor = db.cursor()

            game = TriviaGame(cursor, node)
            response = game.run(msg)

            cursor.close()
            db.commit()

        if response:
            self.send_dm(response, node)
        else:
            self.send_dm("Game error.", node)
