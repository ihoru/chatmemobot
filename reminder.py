from collections import defaultdict
from datetime import date, datetime, timedelta
from glob import glob

from telegram import Bot

import settings
from utils import convert_date, history_dict, plural_phrase

bot = Bot(token=settings.TELEGRAM_BOT_API)


# search message id of certain date
def get_message_id(chat_id, date):
    dictionary = history_dict(chat_id)
    return dictionary.get(date.strftime('%Y-%m-%d'))


# search message id of certain age and reply
def remind(chat_id, days):
    remind_date = convert_date(datetime.utcnow()) - timedelta(days=days)
    message_id = get_message_id(chat_id, remind_date)
    if not message_id:
        return
    text = '{} назад'.format(plural_phrase(days, 'день', 'дня', 'дней'))
    try:
        message = bot.send_message(chat_id, text, reply_to_message_id=message_id)
        return message.message_id
    except Exception:
        pass


# checks messages year by year
def remind_yearly(chat_id, date):
    year_now = int(date.strftime('%Y'))
    dictionary = history_dict(chat_id)
    reminder_ids = []
    for key, message_id in dictionary.items():
        year, month, day = key.split('-')
        year = int(year)
        if year != year_now and month == date.strftime('%m') and day == date.strftime('%d'):
            years = year_now - int(year)
            text = 'В этот день {} назад'.format(plural_phrase(years, 'год', 'года', 'лет'))
            try:
                message = bot.send_message(chat_id, text, reply_to_message_id=message_id)
            except Exception:
                continue
            reminder_ids.append(message.message_id)

    return reminder_ids


# add reminder id to Reminders file
def store_reminder(file, date, message_id):
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = defaultdict(list)
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n').split(',')
    dictionary[date_key].append(message_id)
    file.truncate(0)
    for date_key, message_ids in sorted(dictionary.items()):
        file.write('{}:{}\n'.format(date_key, ','.join(map(str, message_ids))))


# return ids of reminders of certain age
def get_reminder_message_ids(file, date):
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = {}
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n').split(',')
    return dictionary.get(date_key) or []


# delete line from file
def delete_line(file, date):
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = {}
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n')
    if date_key in dictionary.keys():
        del dictionary[date_key]
    file.truncate(0)
    for key, value in sorted(dictionary.items()):
        file.write('{}:{}\n'.format(key, value))


# removes message id from reminders file
def delete_message_id(file, message_id):
    file.seek(0)
    dictionary = {}
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n').split(',')
    for value in dictionary.values():
        if message_id in value:
            value.remove(message_id)


def main():
    for filename in glob('data/-*_history.txt'):
        # TODO: переписать, чтобы в файл производилась запись только один раз в конце.
        # А также считывание из history происходило только раз
        filename = filename.replace('_history.', '_reminders.')
        reminders = open(filename, 'a+')
        chat_id = filename.split('/')[1].split('_')[0]
        today = convert_date(datetime.utcnow())
        yearly_reminder_ids = remind_yearly(chat_id, today)
        for message_id in yearly_reminder_ids:
            store_reminder(reminders, today, message_id)
        for days in settings.REMIND_AFTER_DAYS:
            reminder_id = remind(chat_id, days)
            if reminder_id:
                store_reminder(reminders, today, reminder_id)
        delete_date = today - timedelta(days=settings.DELETE_REMINDER_AFTER_DAYS)
        message_ids = get_reminder_message_ids(reminders, delete_date)
        for message_id in message_ids:
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
        delete_line(reminders, delete_date)
        reminders.close()


if __name__ == '__main__':
    main()
