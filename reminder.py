from copy import copy
from datetime import date, datetime, timedelta
from glob import glob

from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, rrule
from telegram import Bot

import settings
from utils import History, Reminders, convert_date, plural_phrase

bot = Bot(token=settings.TELEGRAM_BOT_API)


def remind(chat_id: int, text: str, message_id):
    try:
        message = bot.send_message(chat_id, text, reply_to_message_id=message_id)
        return message.message_id
    except Exception:
        pass


def delete_message(chat_id, message_id):
    try:
        return bot.delete_message(chat_id, message_id)
    except Exception:
        return False


def lovely_duration(d1: date, d2: date):
    d1 - d2
    rel = relativedelta(dt1=d1, dt2=d2)
    text = ''
    years = rel.years
    months = rel.months
    if years:
        text += '{} {}'.format(years, plural_phrase(years, 'год', 'года', 'лет'))
    if months:
        text += ', {} {}'.format(months, plural_phrase(months, 'месяц', 'месяца', 'месяцев'))
    text += ' назад ({})'.format(d1)
    return text.strip(' ,')


def main():
    today = convert_date(datetime.utcnow()).date()
    yesterday = today - timedelta(days=1)
    for filename in glob('data/-*_history.txt'):
        # проходим по всем файлам с историей сообщений
        chat_id = int(filename.split('/')[1].split('_')[0])
        history = History(chat_id)
        reminders = Reminders(chat_id)
        for months in settings.REMIND_MONTHS:
            # генерируем дату N месяцев назад от сегодня и от вчера, нам нужны даты внутри этого промежутка
            from_dates = yesterday - relativedelta(months=months) + timedelta(days=1)
            till_dates = today - relativedelta(months=months)
            for d in rrule(DAILY, dtstart=from_dates, until=till_dates):
                d = d.date()
                old_message_id = history.get(d)
                if old_message_id:
                    text = lovely_duration(d, today)
                    message_id = remind(chat_id, text, old_message_id)
                    if message_id:
                        reminders.add(today, message_id)
        # удаление старых напоминаний
        delete_date = today - timedelta(days=settings.DELETE_REMINDER_AFTER_DAYS)
        for d, message_ids in copy(reminders.data).items():
            if d <= delete_date:
                del reminders.data[d]
                for message_id in message_ids:
                    delete_message(chat_id, message_id)
        reminders.save()


if __name__ == '__main__':
    main()
