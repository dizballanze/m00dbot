import itertools

from tests.base import BaseTestCase
from storage import QuizStorage
from quizes import HARSQuiz, MADRSQuiz
from questions import HARS_QUESTIONS, MADRS_QUESTIONS


class QuizStorageTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.storage = QuizStorage(self.db_name)

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
        self.storage.create_quiz(chat_id, 'madrs')
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
