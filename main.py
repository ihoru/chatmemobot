import os
from datetime import datetime
import pytz
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
import logging

import settings

updater = Updater(token=settings.TELEGRAM_BOT_API, use_context=True)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
dispatcher = updater.dispatcher


# create a folder to store data
try:
    os.mkdir('data')
except FileExistsError:
    print("Directory already exists")


def save_message_id(file, date, message_id, rewrite=False):
    """
    add (replace - if date already exists) message id to history file
    """
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = dict()
    for line in file:
        pair = line.split(":")
        dictionary[pair[0]] = pair[1].rstrip("\n")
    if date_key in dictionary:
        if not rewrite:
            return 'Такая дата уже есть'
        result = "Обновлено сообщение для даты {}".format(date_key)
    else:
        result = "Сохранено сообщение для даты {}".format(date_key)
    dictionary[date_key] = message_id
    file.truncate(0)
    for key, value in sorted(dictionary.items()):
        file.write("{}:{}\n".format(key, value))
    return result

# get date from message text if any
def get_custom_date(text, default_date):
    if not text:
        return default_date
    try:
        return datetime.strptime(text[:10], '%Y-%m-%d')
    except ValueError:
        return default_date

# converts date without timezone to Bangkok timezone
def convert_date(date):
    naive_date = date
    utc_date = pytz.utc.localize(naive_date)
    bangkok_date = utc_date.astimezone(pytz.timezone('Asia/Bangkok'))
    return bangkok_date


# if chat type is supergroup, try to add message id to history file. Any other chat type - answer with a default text
def answer(update, context):
    effective_chat=update.effective_chat
    if effective_chat.type == 'group':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Добавь меня в групповой чат, я буду записывать и потом напоминать о том, что обсуждалось в чате некоторое время назад.")
        return
    if effective_chat.type != 'supergroup':
        context.bot.send_message(chat_id=update.effective_chat.id, text="Добавь меня в групповой чат, я буду записывать и потом напоминать о том, что обсуждалось в чате некоторое время назад.")
        return
    message = update.message
    with open("data/%s_history.txt" % message.chat_id, "a+") as history:
        custom_date = get_custom_date(message.text or message.caption, convert_date(message.date))
        save_message_id(history, custom_date, message.message_id)


# for command 'save': add (replace - if date already exists) message id to history file
def save_command(update, context):
    effective_chat=update.effective_chat
    bot=context.bot
    reply_to_message = update.message.reply_to_message
    if not reply_to_message:
        bot.send_message(chat_id=effective_chat.id, text="Сделай реплай на сообщение")
        return
    with open("data/%s_history.txt" % update.message.chat_id, "a+") as history:
        message_id = str(reply_to_message.message_id)
        custom_date = get_custom_date(reply_to_message.text or reply_to_message.caption, convert_date(reply_to_message.date))
        result = save_message_id(history, custom_date, message_id, rewrite=True)
        bot.send_message(chat_id=effective_chat.id, text=result)


dispatcher.add_handler(CommandHandler('start', answer))
dispatcher.add_handler(CommandHandler('save', save_command))
dispatcher.add_handler(MessageHandler(Filters.command, answer))
dispatcher.add_handler(MessageHandler(Filters.text, answer))

updater.start_polling()
