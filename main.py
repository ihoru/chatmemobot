import logging
import os
from argparse import ArgumentParser
from datetime import datetime

from telegram import Bot, Chat, Message, Update
from telegram.ext import CallbackContext, CommandHandler, Dispatcher, Filters, MessageHandler, Updater

import settings
from utils import convert_date, file_history

logger=logging.getLogger(__name__)

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
    with file_history(message.chat_id) as history:
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
    with file_history(update.message.chat_id) as history:
        message_id = str(reply_to_message.message_id)
        text = reply_to_message.text or reply_to_message.caption
        custom_date = get_custom_date(text, convert_date(reply_to_message.date))
        result_text = save_message_id(history, custom_date, message_id, rewrite=True)
        message.reply_text(result_text)


def error(update: Update, context: CallbackContext):
    if isinstance(context.error, Stop):
        # остановка
        return
    logger.exception(context.error)
    if update:
        message = update.effective_message  # type:Message
        message.reply_text('Произошла ошибка')


def main():
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    os.makedirs('data', exist_ok=True)

    updater = Updater(token=settings.TELEGRAM_BOT_API, use_context=True)
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)
    dispatcher = updater.dispatcher  # type:Dispatcher
    dispatcher.add_handler(CommandHandler('start', answer))
    dispatcher.add_handler(CommandHandler('save', save_command))
    dispatcher.add_handler(MessageHandler(Filters.update.message & (Filters.text | Filters.caption), answer))
    dispatcher.add_error_handler(error)
    updater.start_polling(allowed_updates=['message'])
    # TODO: try-except KeyboardInterrupt


if __name__ == '__main__':
    main()
