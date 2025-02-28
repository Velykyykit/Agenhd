import telebot
from config.settings import TOKEN  # Імпортуємо токен із конфігурації
from config.auth import register_auth_handlers  # Реєструємо обробники аутентифікації
from menu.keyboards import get_phone_keyboard  # Імпортуємо клавіатуру для запиту телефону

# Ініціалізація бота
bot = telebot.TeleBot(TOKEN)

# Реєстрація обробників команд
def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(
            message.chat.id,
            "Вітаємо! Натисніть кнопку, щоб поділитися номером телефону:",
            reply_markup=get_phone_keyboard()
        )

    @bot.message_handler(content_types=["contact"])
    def verify_phone(message):
        """Обробка номера телефону користувача"""
        if message.contact:
            phone_number = message.contact.phone_number
            bot.send_message(message.chat.id, f"✅ Ваш номер {phone_number} отримано та перевіряється...")
        else:
            bot.send_message(message.chat.id, "❌ Помилка! Будь ласка, скористайтесь кнопкою для відправки номера.")

# Підключення обробників
register_handlers(bot)

# Запуск бота
if __name__ == "__main__":
    print("Бот запущено. Очікування повідомлень...")
    bot.polling(none_stop=True)
