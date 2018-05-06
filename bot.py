import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from storage import HARSQuizStorage, MADRSQuizStorage


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def send_question(question, bot, chat_id):
    keyboard = [[InlineKeyboardButton(answer, callback_data=i)] for i, answer in enumerate(question.answers)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(text=question.question, reply_markup=reply_markup, chat_id=chat_id)


def hars_quiz(bot, update, chat_data):
    chat_data['quiz_type'] = 'hars'
    quiz = hars_quiz_storage.get_or_create(update.message.chat_id, 'ru')
    question = quiz.get_question()
    send_question(question, bot, update.message.chat_id)


def madrs_quiz(bot, update, chat_data):
    chat_data['quiz_type'] = 'madrs'
    quiz = madrs_quiz_storage.get_or_create(update.message.chat_id, 'ru')
    question = quiz.get_question()
    send_question(question, bot, update.message.chat_id)


def process_answer(bot, update, chat_data):
    query = update.callback_query
    bot.edit_message_text(
        text="{}\n{}".format(query.message.text, query.data), chat_id=query.message.chat_id,
        message_id=query.message.message_id)
    if chat_data['quiz_type'] == 'hars':
        storage = hars_quiz_storage
    elif chat_data['quiz_type'] == 'madrs':
        storage = madrs_quiz_storage
    quiz = storage.get_or_create(query.message.chat_id, 'ru')
    quiz.save_answer(int(query.data))
    if quiz.is_completed:
        bot.send_message(chat_id=query.message.chat_id, text="🏁\n{}".format(quiz.get_result()))
    else:
        question = quiz.get_question()
        send_question(question, bot, query.message.chat_id)


if __name__ == '__main__':
    hars_quiz_storage = HARSQuizStorage()
    madrs_quiz_storage = MADRSQuizStorage()
    updater = Updater(token='593799930:AAFSA4HCCiwZkeDbywe_MTu-e1LqN-1ZCJQ')
    dispatcher = updater.dispatcher
    start_hars_quiz_handler = CommandHandler('hars', hars_quiz, pass_chat_data=True)
    dispatcher.add_handler(start_hars_quiz_handler)
    start_madrs_quiz_handler = CommandHandler('madrs', madrs_quiz, pass_chat_data=True)
    dispatcher.add_handler(start_madrs_quiz_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(process_answer, pass_chat_data=True))
    updater.start_polling()
