import pytz


def file_history(chat_id):
    return open('data/{}_history.txt'.format(chat_id), 'a+')


def history_dict(chat_id) -> dict:
    dictionary = {}
    with file_history(chat_id) as history:
        for line in history:
            pair = line.split(':')
            dictionary[pair[0]] = pair[1].rstrip('\n')
    return dictionary


# converts date without timezone to Bangkok timezone
def convert_date(d):
    return d.astimezone(pytz.timezone('Asia/Bangkok'))


def plural_phrase(n, one, two, five):
    if n % 10 == 1 and n % 100 != 11:
        phrase = one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        phrase = two
    else:
        phrase = five
    return '{} {}'.format(n, phrase)
