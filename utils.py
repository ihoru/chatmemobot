from collections import defaultdict
from datetime import date, datetime

import pytz

import settings


class File:
    filename = None
    file = None
    data = None

    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'a+')
        self.read()

    def read(self):
        self.data = dict()
        self.file.seek(0)
        for line in self.file.readlines():
            pair = line.split(':')
            if len(pair) != 2:
                continue
            self.data[pair[0]] = pair[1].strip()

    def save(self):
        self.file.truncate(0)
        for key, value in self._get_data_for_saving():
            self.file.write('{}:{}\n'.format(key, value))
        self.close()

    def add(self, key, value):
        self.data[key] = value

    def has(self, key):
        return key in self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def _get_data_for_saving(self):
        return sorted(self.data.items())

    def close(self):
        self.file.close()


class ChatIdFile(File):
    filename_template = 'data/{}...'

    def __init__(self, chat_id: int):
        filename = self.filename_template.format(chat_id)
        super().__init__(filename)

    def read(self):
        super().read()
        data = self.data
        self.data = dict()
        for k, v in data.items():
            k = datetime.strptime(k, '%Y-%m-%d').date()
            self.data[k] = v

    def add(self, key: date, value):
        assert isinstance(key, date)
        super().add(key, value)

    def _get_data_for_saving(self):
        return [
            (k.strftime('%Y-%m-%d'), v)
            for k, v in sorted(self.data.items())
        ]


class History(ChatIdFile):
    filename_template = 'data/{}_history.txt'


class Reminders(ChatIdFile):
    filename_template = 'data/{}_reminders.txt'

    def read(self):
        super().read()
        data = self.data
        self.data = defaultdict(list)
        for k, v in data.items():
            self.data[k] = list(filter(bool, map(int, str(v).split(','))))

    def add(self, d: date, message_id: int):
        self.data[d].append(message_id)

    def _get_data_for_saving(self):
        return [
            (k.strftime('%Y-%m-%d'), ','.join(map(str, v)))
            for k, v in sorted(self.data.items())
        ]


# convert to my timezone
def convert_date(dt: datetime):
    return dt.astimezone(pytz.timezone(settings.TZ))


def plural_phrase(n, one, two, five):
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        phrase = one
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        phrase = two
    else:
        phrase = five
    return phrase
