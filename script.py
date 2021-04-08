from collections import defaultdict
from datetime import datetime, timedelta

import pytz
from telegram import Bot
from telegram.error import BadRequest

import settings

bot = Bot(token=settings.TELEGRAM_BOT_API)

# CONFIG
remind_ages = [30, 90]
chat_ids = ['-1001456020556']  # TODO: убрать хардкод, сканировать папку на наличие файлов
reminder_age = 7  # days, older reminders will be deleted


# converts date without timezone to Bangkok timezone
def convert_date(date):
    naive_date = date
    utc_date = pytz.utc.localize(naive_date)
    bangkok_date = utc_date.astimezone(pytz.timezone('Asia/Bangkok'))
    return bangkok_date


# search message id of certain date
def get_message_id(file, date):
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = {}
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1]
    try:
        return dictionary[date_key]
    except KeyError:
        return False


def plural_years(n):
    years = ['год', 'года', 'лет']
    if n % 10 == 1:
        p = 0
    elif 1 < n % 10 < 5:
        p = 1
    else:
        p = 2
    return str(n) + ' ' + years[p]


def plural_days(n):
    days = ['день', 'дня', 'дней']

    if n % 10 == 1 and n % 100 != 11:
        p = 0
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        p = 1
    else:
        p = 2

    return str(n) + ' ' + days[p]


# search message id of certain age and reply
def remind(chat_id, age):
    history = open('data/{}_history.txt'.format(chat_id), 'a+')
    remind_date = convert_date(datetime.utcnow()) - timedelta(age)
    message_id = get_message_id(history, remind_date)
    if message_id:
        sent = bot.send_message(
            chat_id=chat_id,
            reply_to_message_id=message_id,
            text='{} назад'.format(plural_days(age)),
        )
        return str(sent.message_id)
    else:
        return False


# checks messages year by year
def remind_yearly(chat_id, date):
    history = open('data/{}_history.txt'.format(chat_id), 'a+')
    date_key = date.strftime('%m-%d')
    year_now = date.strftime('%Y')
    history.seek(0)
    dictionary = {}
    for line in history:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n')
    reminder_ids = []
    for key in dictionary.keys():
        if key[5:10] == date_key:
            message_year = key[:4]
            age = int(year_now) - int(message_year)
            message_id = dictionary[key]
            sent = bot.send_message(
                chat_id=chat_id,
                reply_to_message_id=message_id,
                text='В этот день {} назад'.format(plural_years(age)),
            )
            reminder_ids.append(str(sent.message_id))
    if len(reminder_ids) > 0:
        return reminder_ids
    else:
        return False


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
    for key, value in sorted(dictionary.items()):
        file.write('{}:{}\n'.format(key, ','.join(value)))


# return ids of reminders of certain age
def get_reminder_id(file, age):
    date_today = convert_date(datetime.utcnow())
    date = date_today - timedelta(age)
    date_key = date.strftime('%Y-%m-%d')
    file.seek(0)
    dictionary = {}
    for line in file:
        pair = line.split(':')
        dictionary[pair[0]] = pair[1].rstrip('\n').split(',')
    try:
        return dictionary[date_key]
    except KeyError:
        return []


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
    for chat_id in chat_ids:
        reminders = open('data/{}_reminders.txt'.format(chat_id), 'a+')
        date_today = convert_date(datetime.utcnow())
        yearly_reminder_ids = remind_yearly(chat_id, date_today)
        if yearly_reminder_ids:
            for id in yearly_reminder_ids:
                store_reminder(reminders, date_today, id)
        for age in remind_ages:
            reminder_id = remind(chat_id, age)
            if reminder_id:
                store_reminder(reminders, date_today, reminder_id)
        messages = get_reminder_id(reminders, reminder_age)
        for message in messages:
            try:
                bot.delete_message(chat_id=chat_id, message_id=message)
            except BadRequest:
                pass
        delete_date = convert_date(datetime.utcnow()) - timedelta(reminder_age)
        delete_line(reminders, delete_date)
        reminders.close()


main()
