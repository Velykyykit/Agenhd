from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from menu.keyboards import get_restart_keyboard  # Імпортуємо кнопку "Почати спочатку"

def get_sklad_menu(user_id):
    """Меню складу з ID користувача."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Зробити Замовлення", callback_data=f"order_{user_id}"))
    markup.add(InlineKeyboardButton("📊 Перевірити Наявність", callback_data=f"check_stock_{user_id}"))
    return markup

def handle_sklad(bot, message):
    """Функція для обробки складу."""
    user_id = message.chat.id

    # Спочатку відправляємо меню складу
    bot.send_message(user_id, "📦 Ви у розділі складу. Оберіть дію:", reply_markup=get_sklad_menu(user_id))

    # Потім додаємо кнопку "🔄 Почати спочатку"
    bot.send_message(user_id, "🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=get_restart_keyboard())
