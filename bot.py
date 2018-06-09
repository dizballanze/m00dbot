from datetime import datetime
import logging
import os

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

from storage import QuizStorage, ChatStorage
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
        InlineKeyboardButton('Русский {}'.format(b'\xF0\x9F\x87\xB7\xF0\x9F\x87\xBA'.decode()), callback_data='ru')]])
    bot.send_message(
        text='Choose your language / Выберите язык', reply_markup=langs_markup, chat_id=update.message.chat_id)


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


if __name__ == '__main__':
    quiz_storage = QuizStorage(os.environ.get('DB_NAME'))
    chat_storage = ChatStorage(os.environ.get('DB_NAME'))
    updater = Updater(token=os.environ.get('TG_TOKEN'))
    dispatcher = updater.dispatcher
    updater.job_queue.run_repeating(periodic_notifiction_callback, interval=3600, first=0)
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_lang, pattern='(en|ru)'))
    updater.dispatcher.add_handler(CallbackQueryHandler(process_frequency, pattern='(none|daily|weekly)'))
    start_hars_quiz_handler = CommandHandler('hars', hars_quiz)
    dispatcher.add_handler(start_hars_quiz_handler)
    start_madrs_quiz_handler = CommandHandler('madrs', madrs_quiz)
    dispatcher.add_handler(start_madrs_quiz_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_answer, pattern='\d+'))  # noqa
    updater.start_polling()
