from telebot.types import ReplyKeyboardMarkup, KeyboardButton

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
