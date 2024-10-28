"""
questions from https://github.com/uberspot/OpenTriviaQA/
"""

from pathlib import Path
import threading
import sqlite3


from pydantic import BaseModel
from loguru import logger as log

from . import BaseCommand, CommandLoadError, CommandRunError


DDL = [
    """
CREATE TABLE IF NOT EXISTS category (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT
);""",
    """
CREATE TABLE IF NOT EXISTS question (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category INTEGER,
  question TEXT,
  FOREIGN KEY(category) REFERENCES category(id)
);""",
    """
CREATE TABLE IF NOT EXISTS answer (
  question INTEGER,
  choice TEXT, -- a, b, c, etc
  answer TEXT,
  correct BOOLEAN,
  FOREIGN KEY(question) REFERENCES question(id)
)""",
    """
CREATE TABLE IF NOT EXISTS user (
  userid TEXT PRIMARY KEY,
  pending_question INTEGER NULL
  FOREIGN KEY(pending_question) REFERENCES question(id)
);""",
    """
CREATE TABLE IF NOT EXISTS response (
  userid TEXT,
  question INTEGER,
  answer INTEGER,
  timestamp INTEGER,
  correct BOOLEAN,
  FOREIGN KEY (userid) REFERENCES user(userid)
);
""",
]


class Answer(BaseModel):
    text: str
    choice: str
    correct: bool = False


class Question(BaseModel):
    text: str
    answers: list[Answer] = []


class Category(BaseModel):
    title: str
    questions: list[Question] = []


def read_category_file(path: Path) -> Category:
    """
    read one file from OpenTriviaQA/questions
    """
    log.debug(f"Reading {path.name}..")
    category = Category(title=path.name)

    fd = path.open("r", encoding="utf-8", errors="replace")

    question: Question = None
    in_question = False  # whether or not we are currently parsing the question text which can be multi-line
    correct_answer = None

    for ln in fd:
        # skip empty lines if they are not part of the question
        if ln.strip() == "" and not in_question:
            continue

        # this line starts the question
        if ln[:2] == "#Q":
            # tag the correct answer, if we have one
            if question:
                answer: Answer
                for answer in question.answers:
                    if answer.text == correct_answer:
                        answer.correct = True
                # save the question
                category.questions.append(question)

            # reset
            correct_answer = None

            # start a new question
            question = Question(category=category, text=ln[2:].strip())
            in_question = True

        # this line has _the_ answer
        elif ln[:2] == "^ ":
            correct_answer = ln[2:].strip()
            in_question = False

        # this line has an answer
        elif ln[:2] in ("A ", "B ", "C ", "D ", "E ", "F ", "G ") and not in_question:
            answer = Answer(text=ln[2:].strip())
            question.answers.append(answer)

        # some questions are multiline...
        elif len(ln.strip()) > 0:
            answer.text += ln.strip()

    fd.close()
    return category


def read_questions(path: Path) -> list[Category]:
    """
    iterate files in OpenTriviaQA/questions and load all questions
    """
    results: list[Category] = []
    f: Path

    for f in path.iterdir():
        if f.is_dir():
            continue
        results.append(read_category_file(f))
    return results


def create_database(db_path: Path, questions_path: Path, load_questions: bool = False):
    """
    create tables and populate with categories, questions, and answers
    """
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    for statement in DDL:
        cursor.execute(statement)

    if load_questions is False:
        return

    categories: list[Category] = read_questions(questions_path)
    category: Category
    question: Question
    answer: Answer

    log.debug("Writing questions to database..")
    for category in categories:
        log.debug(f"Category '{category.title}'..")
        r = cursor.execute(
            "INSERT INTO categories (name) VALUES (?) RETURNING id",
            (category.title,),
        )
        category_id = r.fetchone()[0]

        for question in category.questions:
            if len(question.text) > 200:
                continue

            r = cursor.execute(
                "INSERT INTO questions (category, question) VALUES (?, ?) RETURNING id",
                (category_id, question.text),
            )
            question_id = r.fetchone()[0]

            for answer in question.answers:
                cursor.execute(
                    "INSERT INTO answers (question, answer, correct) VALUES (?, ?, ?)",
                    (question_id, answer.text, answer.correct),
                )

    cursor.close()
    db.commit()
    db.close()


def load_database(db_path: Path, questions_path: Path):
    """
    used in the load stage of our command
    'path' is the path to a sqlite database file
    if it does not exist, it will be loaded and populated
    """
    if not db_path.exists():
        log.info(
            "Trivia database '{db_path}' does not exist, creating and populating.."
        )

        if not db_path.parent.exists():
            try:
                db_path.parent.mkdir(parents=True, exist_=True)
            except:
                log.error("Failed to create trivia data dir.")
                raise CommandLoadError()

        try:
            create_database(db_path, questions_path=questions_path, load_questions=True)
        except:
            log.error("Failed to create and populate database.")
            raise CommandLoadError()

    # check to see if we have any questions
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    result = cursor.execute(
        """
SELECT categories.name, COUNT(*)
FROM categories, questions
WHERE questions.category = categories.id
GROUP BY categories.name
"""
    )
    category_counts = [(r[0], r[1]) for r in result.fetchall()]
    cursor.close()
    db.close()
    log.debug(f"Category counts: {category_counts}")


class TriviaGame:
    def __init__(self, cursor: sqlite3.Cursor, node: str):
        self.cursor = cursor
        self.node = node

    def run(self, msg: str) -> str:
        """
        parse command
        decide if we should ask or answer
        return response
        """

        if msg.strip() == "":
            return self.ask()

        # TODO this is dumb
        elif len(msg) == 1:
            return self.answer()

        else:
            return "Unknown command"

    def ask(self):
        """
        pick a new question
        store asked question in db
        return question text
        """

        # fetch a new question
        result = self.cursor.execute(
            """
SELECT id, category, question
FROM questions WHERE id NOT IN (SELECT question FROM responses WHERE userid = ?)
ORDER BY RANDOM() LIMIT 1
""",
            (self.node,),
        )
        question_id, category_id, question = result.fetchone()

        # record that we are asking it with an UPSERT
        result = self.cursor.execute(
            """
INSERT INTO user (userid, pending_question) VALUES (:node, :question_id)
ON CONFLICT (userid)
DO UPDATE SET pending_question = :question_id
""",
            {"node": self.node, "question_id": question_id},
        )

        # 

    def answer(self, user: str, answer: str):
        "check letter answer 'a', 'b', 'c', 'd',"

        # if there is no pending question
        # if answer is correct or not
        # record result
        # return result and correct answer if wrong


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
        questions_path = (
            Path(__file__).parent.parent.parent / "OpenTriviaQA" / "categories"
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

    # def shutdown(self):
    #     log.debug("Shutting down trivia database.")
    #     self.database.close()
