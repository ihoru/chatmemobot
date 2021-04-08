import logging
import os
from datetime import datetime

import pytz
from telegram import Bot, Chat, Message, Update
from telegram.ext import CallbackContext, CommandHandler, Dispatcher, Filters, MessageHandler, Updater

import settings

updater = Updater(token=settings.TELEGRAM_BOT_API, use_context=True)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
dispatcher = updater.dispatcher  # type:Dispatcher

# create a folder to store data
try:
    os.mkdir('data')
except FileExistsError:
    print('Directory already exists')


class Stop(Exception):
    pass

def save_message_id(file, date, message_id, rewrite=False):
    """
    add (replace - if date already exists) message id to history file
    """
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = dict()
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n')
    if date_key in dictionary:
        if not rewrite:
            return 'Такая дата уже есть'
        result = 'Обновлено сообщение для даты {}'.format(date_key)
    else:
        result = 'Сохранено сообщение для даты {}'.format(date_key)
    dictionary[date_key] = message_id
    file.truncate(0)
    for key, value in sorted(dictionary.items()):
        file.write('{}:{}\n'.format(key, value))
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
def convert_date(d):
    return d.astimezone(pytz.timezone('Asia/Bangkok'))


def check_chat(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type:Chat
    bot = context.bot  # type:Bot
    if chat.type != Chat.SUPERGROUP:
        bot.send_message(chat.id, 'Добавь меня в групповой чат, я буду записывать и потом напоминать о том, '
                                  'что обсуждалось в чате некоторое время назад.')
        raise Stop


# if chat type is supergroup, try to add message id to history file. Any other chat type - answer with a default text
def answer(update: Update, context: CallbackContext):
    check_chat(update, context)
    message = update.message  # type:Message
    with open('data/{}_history.txt'.format(message.chat_id), 'a+') as history:
        text = message.text or message.caption
        custom_date = get_custom_date(text, convert_date(message.date))
        save_message_id(history, custom_date, message.message_id)


# for command 'save': add (replace - if date already exists) message id to history file
def save_command(update: Update, context: CallbackContext):
    check_chat(update, context)
    message = update.message  # type:Message
    reply_to_message = update.message.reply_to_message  # type:Message
    if not reply_to_message:
        message.reply_text('Сделай реплай на сообщение')
        return
    with open('data/{}_history.txt'.format(update.message.chat_id), 'a+') as history:
        message_id = str(reply_to_message.message_id)
        text = reply_to_message.text or reply_to_message.caption
        custom_date = get_custom_date(text, convert_date(reply_to_message.date))
        result_text = save_message_id(history, custom_date, message_id, rewrite=True)
        message.reply_text(result_text)


def error(update: Update, context: CallbackContext):
    if isinstance(context.error, Stop):
        # остановка
        return
    message = update.effective_message  # type:Message
    message.reply_text('Произошла ошибка')


dispatcher.add_handler(CommandHandler('start', answer))
dispatcher.add_handler(CommandHandler('save', save_command))
dispatcher.add_handler(MessageHandler(Filters.update.message & (Filters.text | Filters.caption), answer))
dispatcher.add_error_handler(error)

updater.start_polling(allowed_updates=['message'])
