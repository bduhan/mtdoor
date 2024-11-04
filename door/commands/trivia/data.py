from pathlib import Path
import sqlite3

from loguru import logger as log
from pydantic import BaseModel

from .. import CommandLoadError


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

    # run SQL
    ddl_file = Path(__file__).with_name("trivia.sql")
    db.executescript(ddl_file.open("r").read())
    db.commit()

    if load_questions is False:
        return

    categories: list[Category] = read_questions(questions_path)
    category: Category
    question: Question
    answer: Answer

    cursor = db.cursor()

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

