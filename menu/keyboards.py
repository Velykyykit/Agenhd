from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def get_phone_keyboard():
    """
    Клавіатура для запиту номера телефону.
    Використовуємо лише кнопку для надання номера телефону.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_button = KeyboardButton("📲 Поділитися номером", request_contact=True)
    markup.add(phone_button)  # Додаємо тільки кнопку для надання номера
    return markup

def get_restart_keyboard():
    """
    Клавіатура для кнопки перезапуску.
    Використовуємо лише кнопку для перезапуску.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    restart_button = KeyboardButton("🔄 Почати спочатку")
    markup.add(restart_button)  # Додаємо тільки кнопку для перезапуску
    return markup
