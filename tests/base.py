import os
import sqlite3
from unittest import TestCase

from db_helpers import dict_factory
from create_db import create_database


class BaseTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.db_name = 'test.db'
        try:
            os.unlink(self.db_name)
        except OSError:
            pass
        create_database(self.db_name)

    def tearDown(self):
        os.unlink(self.db_name)
        super().tearDown()

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
        return conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = dict_factory
        return conn
