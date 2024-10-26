"""

https://github.com/uberspot/OpenTriviaQA/

"""

from pathlib import Path
import sqlite3

from pydantic import BaseModel
from loguru import logger as log

from .base import BaseCommand, CommandLoadError, CommandRunError

DDL = """

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT
);

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category INTEGER,
  question TEXT,
  FOREIGN KEY(category) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS answers (
  question INTEGER,
  answer TEXT,
  correct BOOLEAN,
  FOREIGN KEY(question) REFERENCES question(id)
)

CREATE TABLE IF NOT EXISTS users (
  userid TEXT PRIMARY KEY,
  pending_question INTEGER NULL
);

CREATE_TABLE IF NOT EXISTS responses (
  user TEXT,
  question INTEGER,
  answer INTEGER,
  timestamp INTEGER,
  correct BOOLEAN
  FOREGIN KEY (user) REFERENCES users(userid)
);

"""

class TriviaGame:
    def __init__(self, database: Path):
        self.database = sqlite3.connect(database)
    
    def create_tables(self):
        """ run DDL on database """
        pass
    
    def load_questions(self, path: Path):
        """
        load questions into database from root path cloned from github.com/uberspot/OpenTriviaQA
        """
        pass
    
    def ask(self, user: str):
        """
        generate a new question
        store asked question in session
        """
    
    def answer(self, user: str, answer: str):
        " check letter answer 'a', 'b', 'c', 'd',"

        # if there is no pending question
        # if answer is correct or not
        # record result
    
    def shutdown(self):
        log.debug("Shutting down trivia database.")
        self.database.close()

class TriviaCommand(BaseCommand):
    command = "trivia"
    description = "answer trivia questions"
    help = "Commands: 'skip', 'clear', 'last', 'stats'.\n\nAnswer with 'a', 'b', 'c', etc."
    

    def load(self):
        db_file = Path(__file__).parent.parent / "data" / "trivia.sqlite"

        if not db_file.parent.exists():
            try:
                self.game.parent.mkdir(parents=True, exist_=True)
            except:
                log.exception("Failed to create game data dir")
                raise CommandLoadError()

        self.game = TriviaGame(self.db_file)
    
    def invoke(self, msg: str, node: str) -> str:
        pass