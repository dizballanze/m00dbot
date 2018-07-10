import sqlite3
import datetime

from db_helpers import dict_factory
from quizes import HARSQuiz, MADRSQuiz
from questions import HARS_QUESTIONS, MADRS_QUESTIONS


class BaseStorage:

    def __init__(self, db_name):
        self.db_name = db_name

    def get_conn(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = dict_factory
        return conn


class QuizStorage(BaseStorage):

    def get_latest_quiz(self, chat_id):
        """ Return latest (by id) quiz for specified chat, return filled quiz instance """
        chat_data = ChatStorage(self.db_name).get_chat(chat_id)
        cur = self.get_conn().cursor()
        cur.execute('SELECT * FROM quizes WHERE chat_id = ? ORDER BY id DESC', (chat_data['id'],))
        quiz_data = cur.fetchone()
        return self._create_quiz_instance(
            quiz_data['id'], quiz_data['type'], chat_data['language'], chat_data['created_at'])

    def get_completed_quizes(self, chat_id, **kwargs):
        order, limit = kwargs.get('order', 'ASC'), kwargs.get('limit', '30')
        chat_data = ChatStorage(self.db_name).get_chat(chat_id)
        cur = self.get_conn().cursor()
        cur.execute(
            "SELECT * FROM quizes WHERE (chat_id = ?) AND (type = 'madrs') AND (question_number >= 9) "
            "ORDER BY id {} LIMIT ?".format(order),
            (chat_data['id'], limit))
        quizes_data = list(cur.fetchall())
        cur.execute(
            "SELECT * FROM quizes WHERE (chat_id = ?) AND (type = 'hars') AND (question_number >= 13) "
            "ORDER BY id {} LIMIT ?".format(order),
            (chat_data['id'], limit))
        quizes_data += list(cur.fetchall())
        quiz_instances = []
        for quiz_data in quizes_data:
            quiz_instances.append(self._create_quiz_instance(
                quiz_data['id'], quiz_data['type'], chat_data['language'], quiz_data['created_at']))
        return quiz_instances

    def create_quiz(self, chat_id, type_):
        chat_data = ChatStorage(self.db_name).get_chat(chat_id)
        conn = self.get_conn()
        now_dt_formated = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        conn.execute('INSERT INTO quizes VALUES (?, ?, ?, ?, ?)', (None, chat_id, now_dt_formated, type_, 0))
        conn.commit()
        return self._create_quiz_instance(self._get_last_id(conn), type_, chat_data['language'], [])

    def save_answer(self, quiz, answer):
        question_number = quiz.question_number + 1
        conn = self.get_conn()
        conn.execute(
            'UPDATE quizes SET question_number = ? WHERE id = ?', (question_number, quiz.id))
        conn.execute(
            'INSERT INTO answers (quiz_id, question_number, answer) VALUES (?, ?, ?)',
            (quiz.id, question_number, answer))
        conn.commit()
        quiz.question_number = question_number
        quiz.answers.append(answer)

    def _create_quiz_instance(self, id, type_, lang, created_at=None):
        cur = self.get_conn().cursor()
        cur.execute('SELECT * FROM answers WHERE quiz_id = ? ORDER BY question_number ASC', (id,))
        answers_data = cur.fetchall()
        answers = []
        for answer in answers_data:
            answers.append(answer['answer'])
        if type_ == 'hars':
            quiz_class = HARSQuiz
            questions = HARS_QUESTIONS
        else:
            quiz_class = MADRSQuiz
            questions = MADRS_QUESTIONS
        return quiz_class(id, questions, lang, question_number=len(answers), answers=answers, created_at=created_at)

    def _get_last_id(self, conn):
        return conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']


class ChatStorage(BaseStorage):

    def get_or_create(self, chat_id, language='en', frequency='none'):
        chat_data = self.get_chat(chat_id)
        if chat_data is None:
            now_dt_formated = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
            conn = self.get_conn()
            conn.execute('INSERT INTO chats VALUES (?, ?, ?, ?)', (chat_id, now_dt_formated, frequency, language))
            conn.commit()
            chat_data = self.get_chat(chat_id)
        return chat_data

    def get_chat(self, chat_id):
        cur = self.get_conn().cursor()
        cur.execute('SELECT * FROM chats WHERE id = ?', (chat_id,))
        return cur.fetchone()

    def save(self, chat_data):
        conn = self.get_conn()
        conn.execute(
            'UPDATE chats SET frequency = ?, language = ? WHERE id = ?',
            (chat_data['frequency'], chat_data['language'], chat_data['id']))
        conn.commit()

    def get_chats(self):
        cur = self.get_conn().cursor()
        cur.execute('SELECT * FROM chats')
        return cur.fetchall()
