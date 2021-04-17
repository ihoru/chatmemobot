TELEGRAM_BOT_API = ''
TZ = 'UTC'
REMIND_AFTER_DAYS = [30, 90]  # list of days, reminders will be created
DELETE_REMINDER_AFTER_DAYS = 7  # days, older reminders will be deleted

# noinspection PyUnresolvedReferences
from local_settings import *
assert bool(TELEGRAM_BOT_API), 'local_settings.TELEGRAM_BOT_API must be defined'
