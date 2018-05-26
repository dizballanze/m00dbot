import os
import sqlite3
import itertools
from unittest import TestCase

from storage import QuizStorage
from quizes import HARSQuiz, MADRSQuiz
from create_db import create_database
from questions import HARS_QUESTIONS, MADRS_QUESTIONS


class QuizStorageTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.db_name = 'test.db'
        try:
            os.unlink(self.db_name)
        except FileNotFoundError:
            ...
        create_database(self.db_name)
        self.storage = QuizStorage(self.db_name)

    def tearDown(self):
        os.unlink(self.db_name)
        super().tearDown()

    def test_get_latest_quiz_semi_completed_hars(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='en')
        quiz_id = self._insert_quiz(chat_id, question_number=3, type_='hars')
        for question_number in range(0, 3):
            self._insert_answer(quiz_id, question_number, 2)
        quiz = self.storage.get_latest_quiz(chat_id)
        self.assertIsInstance(quiz, HARSQuiz)
        self.assertDictEqual(quiz.questions, HARS_QUESTIONS)
        self.assertEqual(quiz.lang, 'en')
        self.assertEqual(quiz.question_number, 3)
        self.assertListEqual(quiz.answers, [2, 2, 2])
        self.assertFalse(quiz.is_completed)

    def test_get_latest_quiz_completed_madrs(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='ru')
        quiz_id = self._insert_quiz(chat_id, question_number=10, type_='madrs')
        answers = itertools.cycle(range(0, 7))
        for question_number in range(0, 10):
            self._insert_answer(quiz_id, question_number, next(answers))
        quiz = self.storage.get_latest_quiz(chat_id)
        self.assertIsInstance(quiz, MADRSQuiz)
        self.assertDictEqual(quiz.questions, MADRS_QUESTIONS)
        self.assertEqual(quiz.lang, 'ru')
        self.assertEqual(quiz.question_number, 10)
        self.assertListEqual(quiz.answers, [0, 1, 2, 3, 4, 5, 6, 0, 1, 2])
        self.assertTrue(quiz.is_completed)

    def test_create_quiz_returns_quiz_instance(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='en')
        quiz = self.storage.create_quiz(chat_id, 'hars')
        self.assertIsInstance(quiz, HARSQuiz)
        self.assertDictEqual(quiz.questions, HARS_QUESTIONS)
        self.assertEqual(quiz.lang, 'en')
        self.assertEqual(quiz.question_number, 0)
        self.assertFalse(quiz.is_completed)

    def test_create_quiz_madrs_instance(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='ru')
        quiz = self.storage.create_quiz(chat_id, 'madrs')
        self.assertDictEqual(quiz.questions, MADRS_QUESTIONS)
        self.assertEqual(quiz.lang, 'ru')
        self.assertEqual(quiz.question_number, 0)
        self.assertFalse(quiz.is_completed)

    def test_create_quiz_inserts_quiz_to_db(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='ru')
        quiz = self.storage.create_quiz(chat_id, 'madrs')
        cur = self._get_connection().cursor()
        cur.execute('SELECT * FROM quizes')
        res = cur.fetchone()
        self.assertEqual(res['chat_id'], str(chat_id))
        self.assertEqual(res['type'], 'madrs')
        self.assertEqual(res['question_number'], 0)

    def test_save_answer_updates_quiz_instance(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='ru')
        quiz = self.storage.create_quiz(chat_id, 'madrs')
        self.storage.save_answer(quiz, 1)
        self.storage.save_answer(quiz, 2)
        self.assertEqual(quiz.question_number, 2)
        self.assertListEqual(quiz.answers, [1, 2])

    def test_save_answer_creates_answer_in_database(self):
        chat_id = 31337
        self._insert_chat(chat_id, lang='en')
        quiz = self.storage.create_quiz(chat_id, 'hars')
        self.storage.save_answer(quiz, 0)
        self.storage.save_answer(quiz, 3)
        self.storage.save_answer(quiz, 1)
        quiz_from_db = self.storage.get_latest_quiz(chat_id)
        self.assertEqual(quiz_from_db.question_number, 3)
        self.assertListEqual(quiz_from_db.answers, [0, 3, 1])

    def _insert_chat(self, chat_id, created_at='2018-05-20 12:26:00', frequency='daily', lang='en'):
        conn = self._get_connection()
        conn.execute('INSERT INTO chats VALUES (?, ?, ?, ?)', (chat_id, created_at, frequency, lang))
        conn.commit()
        return chat_id

    def _insert_quiz(self, chat_id, created_at='2018-05-20 12:30:00', type_='hars', question_number=0):
        conn = self._get_connection()
        conn.execute(
            'INSERT INTO quizes (chat_id, created_at, type, question_number) VALUES (?, ?, ?, ?)',
            (chat_id, created_at, type_, question_number))
        conn.commit()
        return self._get_last_id(conn)

    def _insert_answer(self, quiz_id, question_number, answer):
        conn = self._get_connection()
        conn.execute(
            'INSERT INTO answers (quiz_id, question_number, answer) VALUES (?, ?, ?)',
            (quiz_id, question_number, answer))
        conn.commit()
        return self._get_last_id(conn)

    def _get_last_id(self, conn):
        return conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
