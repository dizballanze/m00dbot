from tests.base import BaseTestCase
from storage import ChatStorage


class ChatStorageTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.storage = ChatStorage(self.db_name)

    def test_get_chat(self):
        chat_id = 31337
        self._insert_chat(chat_id, frequency='none', lang='en')
        chat_data = self.storage.get_chat(chat_id)
        self.assertEqual(chat_data['frequency'], 'none')
        self.assertEqual(chat_data['language'], 'en')
        self.assertEqual(chat_data['id'], str(chat_id))

    def test_get_or_create_creates_new_chat(self):
        chat_id = 31337
        self.storage.get_or_create(chat_id, language='ru', frequency='weekly')
        chat_data = self.storage.get_chat(chat_id)
        self.assertEqual(chat_data['frequency'], 'weekly')
        self.assertEqual(chat_data['language'], 'ru')
        self.assertEqual(chat_data['id'], str(chat_id))

    def test_get_or_create_return_existed_chat(self):
        chat_id = 31337
        self._insert_chat(chat_id, frequency='none', lang='en')
        chat_data = self.storage.get_or_create(chat_id)
        self.assertEqual(chat_data['frequency'], 'none')
        self.assertEqual(chat_data['language'], 'en')
        self.assertEqual(chat_data['id'], str(chat_id))

    def test_save_changes(self):
        chat_id = 31337
        self._insert_chat(chat_id, frequency='daily', lang='en')
        chat_data = self.storage.get_chat(chat_id)
        chat_data['frequency'] = 'none'
        chat_data['language'] = 'ru'
        self.storage.save(chat_data)
        chat_data_updated = self.storage.get_chat(chat_id)
        self.assertEqual(chat_data_updated['frequency'], 'none')
        self.assertEqual(chat_data_updated['language'], 'ru')
