import logging
import os
from argparse import ArgumentParser
from datetime import date, datetime

from telegram import *
from telegram.ext import *

import settings
from utils import History, convert_date

logger = logging.getLogger(__name__)


class Stop(Exception):
    pass


# get date from message text if any
def get_custom_date(text: str, default: date):
    if not text:
        return default
    try:
        return datetime.strptime(text[:10], '%Y-%m-%d').date()
    except ValueError:
        return default


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
    text = message.text or message.caption
    custom_date = get_custom_date(text, convert_date(message.date).date())
    history = History(message.chat_id)
    if history.has(custom_date):
        # дата уже есть
        history.close()
    else:
        history.add(custom_date, message.message_id)
        history.save()


# for command 'save': add (replace - if date already exists) message id to history file
def save_command(update: Update, context: CallbackContext):
    check_chat(update, context)
    message = update.message  # type:Message
    reply_to_message = update.message.reply_to_message  # type:Message
    if not reply_to_message:
        message.reply_text('Сделай реплай на сообщение')
        return
    message_id = str(reply_to_message.message_id)
    text = reply_to_message.text or reply_to_message.caption
    custom_date = get_custom_date(text, convert_date(reply_to_message.date).date())
    history = History(message.chat_id)
    history.add(custom_date, message_id)
    history.save()
    if history.has(custom_date):
        reply = 'Обновлено для {}'
    else:
        reply = 'Сохранено для {}'
    reply = reply.format(custom_date)
    message.reply_text(reply)


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
