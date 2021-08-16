TELEGRAM_BOT_API = ''
TZ = 'UTC'
REMIND_MONTHS = [
    # через сколько месяцев напоминать о сообщении
    1, 3, 6,
    # года
    1 * 12,
    2 * 12,
    3 * 12,
    4 * 12,
    5 * 12,
]
DELETE_REMINDER_AFTER_DAYS = 7  # напоминания старее столько дней будут удалены
HELP_URL = 'https://telegra.ph/ChatMemoBot--bot-dnevnik-08-16'
REPOSITORY_URL = 'https://github.com/ihoru/chatmemobot'

# noinspection PyUnresolvedReferences
from local_settings import *
assert bool(TELEGRAM_BOT_API), 'local_settings.TELEGRAM_BOT_API must be defined'
assert DELETE_REMINDER_AFTER_DAYS > 0, 'Напоминания должны повисеть хотя бы день'
