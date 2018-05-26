import logging
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from storage import QuizStorage


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def send_question(question, bot, chat_id):
    keyboard = [[InlineKeyboardButton(answer, callback_data=i)] for i, answer in enumerate(question.answers)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text=question.question, reply_markup=reply_markup, chat_id=chat_id)


def hars_quiz(bot, update, chat_data):
    quiz = quiz_storage.create_quiz(update.message.chat_id, 'hars')
    question = quiz.get_question()
    send_question(question, bot, update.message.chat_id)


def madrs_quiz(bot, update, chat_data):
    quiz = quiz_storage.create_quiz(update.message.chat_id, 'madrs')
    question = quiz.get_question()
    send_question(question, bot, update.message.chat_id)


def process_answer(bot, update, chat_data):
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
        send_question(question, bot, query.message.chat_id)


if __name__ == '__main__':
    quiz_storage = QuizStorage(os.environ.get('DB_NAME'))
    updater = Updater(token=os.environ.get('TG_TOKEN'))
    dispatcher = updater.dispatcher
    start_hars_quiz_handler = CommandHandler('hars', hars_quiz, pass_chat_data=True)
    dispatcher.add_handler(start_hars_quiz_handler)
    start_madrs_quiz_handler = CommandHandler('madrs', madrs_quiz, pass_chat_data=True)
    dispatcher.add_handler(start_madrs_quiz_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_answer, pass_chat_data=True))
    updater.start_polling()
