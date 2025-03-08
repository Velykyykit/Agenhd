from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def get_phone_keyboard():
    """
    Клавіатура для запиту номера телефону.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Поділитися номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

async def get_restart_keyboard():
    """
    Клавіатура для кнопки перезапуску.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔄 Почати спочатку")]],
        resize_keyboard=True
    )
