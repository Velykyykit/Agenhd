from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_phone_keyboard():
    """
    Клавіатура для запиту номера телефону.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_button = KeyboardButton("📲 Поділитися номером", request_contact=True)
    restart_button = KeyboardButton("🔄 Почати спочатку")
    markup.add(phone_button)
    markup.add(restart_button)
    return markup

def get_restart_keyboard():
    """
    Клавіатура для повернення на початок.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    restart_button = KeyboardButton("🔄 Почати спочатку")
    markup.add(restart_button)
    return markup

def remove_keyboard():
    """
    Видаляє клавіатуру (наприклад, після авторизації).
    """
    return ReplyKeyboardRemove()
