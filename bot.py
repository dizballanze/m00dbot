from datetime import datetime
import logging
import os

import telegram.bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.ext import messagequeue as mq
from telegram.utils.request import Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

from storage import QuizStorage, ChatStorage
from export import get_quizes_plot, get_csv
import texts


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def help(bot, update):
    print(update.message.chat_id)
    lang = chat_storage.get_or_create(update.message.chat_id)['language']
    bot.send_message(text=texts.INTRO[lang], chat_id=update.message.chat_id)


def start(bot, update):
    # Select language
    langs_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton('English {}'.format(b'\xF0\x9F\x87\xAC\xF0\x9F\x87\xA7'.decode()), callback_data='en'),
        InlineKeyboardButton('Русский {}'.format(b'\xF0\x9F\x87\xB7\xF0\x9F\x87\xBA'.decode()), callback_data='ru'),
        InlineKeyboardButton('Português {}'.format(b'\xF0\x9F\x87\xA7\xF0\x9F\x87\xB7'.decode()), callback_data='pt'),
        InlineKeyboardButton('Italian {}'.format(b'\xF0\x9F\x87\xAE\xF0\x9F\x87\xB9'.decode()), callback_data='it')
    ]])
    bot.send_message(
        text='Choose your language / Выберите язык / Escolha seu idioma / Scegli la tua lingua',
        reply_markup=langs_markup,
        chat_id=update.message.chat_id,
    )


def process_lang(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        text="{}\n{}".format(query.message.text, query.data), chat_id=query.message.chat_id,
        message_id=query.message.message_id)
    chat = chat_storage.get_or_create(query.message.chat_id)
    chat['language'] = query.data
    chat_storage.save(chat)
    send_frequency_question(bot, query.message.chat_id)


def send_frequency_question(bot, chat_id):
    lang = chat_storage.get_or_create(chat_id)['language']
    frequency_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(texts.FREQUENCY_NONE[lang], callback_data='none'),
        InlineKeyboardButton(texts.FREQUENCY_DAILY[lang], callback_data='daily'),
        InlineKeyboardButton(texts.FREQUENCY_WEEKLY[lang], callback_data='weekly')]])
    bot.send_message(text=texts.FREQUENCY_QUESTION[lang], reply_markup=frequency_markup, chat_id=chat_id)


def process_frequency(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        text="{}\n{}".format(query.message.text, query.data), chat_id=query.message.chat_id,
        message_id=query.message.message_id)
    chat = chat_storage.get_or_create(query.message.chat_id)
    chat['frequency'] = query.data
    chat_storage.save(chat)
    send_intro(bot, query.message.chat_id)


def send_intro(bot, chat_id):
    lang = chat_storage.get_or_create(chat_id)['language']
    bot.send_message(text=texts.INTRO[lang], chat_id=chat_id)


def send_hars_question(question, bot, chat_id):
    keyboard = [[InlineKeyboardButton(answer, callback_data=i)] for i, answer in enumerate(question.answers)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text=question.question, reply_markup=reply_markup, chat_id=chat_id)


def hars_quiz(bot, update):
    quiz = quiz_storage.create_quiz(update.message.chat_id, 'hars')
    question = quiz.get_question()
    lang = chat_storage.get_or_create(update.message.chat_id)['language']
    bot.send_message(text=texts.HARS_INTRO[lang], chat_id=update.message.chat_id)
    send_hars_question(question, bot, update.message.chat_id)


def send_madrs_question(question, bot, chat_id):
    keyboard = [[InlineKeyboardButton(str(i), callback_data=i) for i in range(0, 7)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    question_text = '{}\n{}'.format(question.question, '\n'.join(question.answers))
    bot.send_message(text=question_text, reply_markup=reply_markup, chat_id=chat_id)


def madrs_quiz(bot, update):
    quiz = quiz_storage.create_quiz(update.message.chat_id, 'madrs')
    question = quiz.get_question()
    lang = chat_storage.get_or_create(update.message.chat_id)['language']
    bot.send_message(text=texts.MADRS_INTRO[lang], chat_id=update.message.chat_id)
    send_madrs_question(question, bot, update.message.chat_id)


def process_answer(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        text="{}\n{}".format(query.message.text, query.data), chat_id=query.message.chat_id,
        message_id=query.message.message_id)
    quiz = quiz_storage.get_latest_quiz(query.message.chat_id)
    quiz_storage.save_answer(quiz, int(query.data))
    if quiz.is_completed:
        bot.send_message(chat_id=query.message.chat_id, text="🏁\n{}".format(quiz.get_result()))
    else:
        question = quiz.get_question()
        if quiz.type_ == 'hars':
            send_hars_question(question, bot, query.message.chat_id)
        else:
            send_madrs_question(question, bot, query.message.chat_id)


def periodic_notifiction_callback(bot, job):
    for chat in chat_storage.get_chats():
        if chat['frequency'] == 'none':
            continue
        created_at = datetime.strptime(chat['created_at'], '%Y-%m-%d %H-%M-%S')
        now = datetime.now()
        if created_at.hour != now.hour:
            continue
        if (chat['frequency'] == 'weekly') and (now.weekday() != created_at.weekday()):
            continue
        try:
            bot.send_message(chat_id=chat['id'], text=texts.PERIODIC_NOTIFICATION[chat['language']])
        except BadRequest:
            pass


def export(bot, update):
    keyboard = [[InlineKeyboardButton('PNG', callback_data='png'), InlineKeyboardButton('CSV', callback_data='csv')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    lang = chat_storage.get_or_create(update.message.chat_id)['language']
    bot.send_message(text=texts.EXPORT[lang], reply_markup=reply_markup, chat_id=update.message.chat_id)


def process_export(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        text="{} {}".format(query.message.text, query.data), chat_id=query.message.chat_id,
        message_id=query.message.message_id)
    if query.data == 'png':
        quizes = quiz_storage.get_completed_quizes(query.message.chat_id, order='DESC')
        plot = get_quizes_plot(quizes)
        bot.send_photo(chat_id=query.message.chat_id, photo=plot)
    if query.data == 'csv':
        quizes = quiz_storage.get_completed_quizes(query.message.chat_id, limit=999)
        csv_buf = get_csv(quizes)
        bot.send_document(chat_id=query.message.chat_id, document=csv_buf, filename='m00d.csv')


class MQBot(telegram.bot.Bot):

    """ A subclass of Bot which delegates send method handling to MQ """

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        self._msg_queue.stop()
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        return super(MQBot, self).send_message(*args, **kwargs)

    @mq.queuedmessage
    def edit_message_text(self, *args, **kwargs):
        return super().edit_message_text(*args, **kwargs)


if __name__ == '__main__':
    quiz_storage = QuizStorage(os.environ.get('DB_NAME'))
    chat_storage = ChatStorage(os.environ.get('DB_NAME'))
    q = mq.MessageQueue(all_burst_limit=30, all_time_limit_ms=3000)
    request = Request(con_pool_size=8)
    m00dbot = MQBot(os.environ.get('TG_TOKEN'), request=request, mqueue=q)
    updater = Updater(bot=m00dbot)
    dispatcher = updater.dispatcher
    updater.job_queue.run_repeating(periodic_notifiction_callback, interval=3600, first=0)
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_lang, pattern='(en|ru|pt|it)'))
    updater.dispatcher.add_handler(CallbackQueryHandler(process_frequency, pattern='(none|daily|weekly)'))
    start_hars_quiz_handler = CommandHandler('hars', hars_quiz)
    dispatcher.add_handler(start_hars_quiz_handler)
    start_madrs_quiz_handler = CommandHandler('madrs', madrs_quiz)
    dispatcher.add_handler(start_madrs_quiz_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_answer, pattern='\d+'))  # noqa
    export_handler = CommandHandler('export', export)
    dispatcher.add_handler(export_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_export, pattern='(png|csv)'))
    updater.start_polling()
