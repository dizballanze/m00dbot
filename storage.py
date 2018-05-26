import os
import sqlite3
import datetime

from quizes import HARSQuiz, MADRSQuiz
from questions import HARS_QUESTIONS, MADRS_QUESTIONS


class QuizStorage:

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row

    def get_latest_quiz(self, chat_id):
        """ Return latest (by id) quiz for specified chat, return filled quiz instance """
        chat_data = self._get_chat_data(chat_id)
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM quizes WHERE chat_id = ? ORDER BY id DESC', (chat_data['id'],))
        quiz_data = cur.fetchone()
        cur.execute('SELECT * FROM answers WHERE quiz_id = ? ORDER BY question_number ASC', (quiz_data['id'],))
        answers_data = cur.fetchall()
        answers = []
        for answer in answers_data:
            answers.append(answer['answer'])
        return self._create_quiz_instance(quiz_data['type'], chat_data['language'], answers)

    def create_quiz(self, chat_id, type_):
        chat_data = self._get_chat_data(chat_id)
        self.conn.execute(
            "INSERT INTO quizes (chat_id, created_at, type, question_number) VALUES (?, ?, ?, ?)",
            (chat_id, datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S'), type_, 0))
        self.conn.commit()
        return self._create_quiz_instance(type_, chat_data['language'], [])

    def save_answer(self, quiz, answer):
        # Save answer to DB and update quiz instance
        ...

    def _get_chat_data(self, chat_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM chats WHERE id = ?', (chat_id,))
        return cur.fetchone()

    def _create_quiz_instance(self, type_, lang, answers):
        if type_ == 'hars':
            quiz_class = HARSQuiz
            questions = HARS_QUESTIONS
        else:
            quiz_class = MADRSQuiz
            questions = MADRS_QUESTIONS
        return quiz_class(questions, lang, question_number=len(answers), answers=answers)
