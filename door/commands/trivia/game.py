import sqlite3

from .data import Category, Question, Answer

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

