from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_sklad_menu(user_id):
    """Меню складу з ID користувача."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Зробити Замовлення", callback_data=f"order_{user_id}"))
    markup.add(InlineKeyboardButton("📊 Перевірити Наявність", callback_data=f"check_stock_{user_id}"))
    return markup

def get_restart_keyboard():
    """Клавіатура для кнопки перезапуску."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    restart_button = KeyboardButton("🔄 Почати спочатку")
    markup.add(restart_button)  # Додаємо кнопку у вигляді клавіатури
    return markup

