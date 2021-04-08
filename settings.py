TELEGRAM_BOT_API = ''

# noinspection PyUnresolvedReferences
from local_settings import *
assert bool(TELEGRAM_BOT_API), 'local_settings.TELEGRAM_BOT_API must be defined'
