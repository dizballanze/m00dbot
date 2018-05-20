import os
import sqlite3

from quizes import HARSQuiz, MADRSQuiz
from questions import HARS_QUESTIONS, MADRS_QUESTIONS


class QuizStorage:

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row

    def get_latest_quiz(self, chat_id):
        """ Return latest (by id) quiz for specified chat, return filled quiz instance """
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM chats WHERE id = ?', (chat_id,))
        chat_data = cur.fetchone()
        cur.execute('SELECT * FROM quizes WHERE chat_id = ? ORDER BY id DESC', (chat_data['id'],))
        quiz_data = cur.fetchone()
        cur.execute('SELECT * FROM answers WHERE quiz_id = ? ORDER BY question_number ASC', (quiz_data['id'],))
        answers_data = cur.fetchall()
        answers = []
        for answer in answers_data:
            answers.append(answer['answer'])
        if quiz_data['type'] == 'hars':
            quiz_class = HARSQuiz
            questions = HARS_QUESTIONS
        else:
            quiz_class = MADRSQuiz
            questions = MADRS_QUESTIONS
        return quiz_class(questions, chat_data['language'], question_number=len(answers), answers=answers)

    def create_quiz(self, chat_id, type_):
        # Create quiz of specified type in DB and return quiz instance
        ...

    def save_answer(self, quiz, answer):
        # Save answer to DB and update quiz instance
        ...
