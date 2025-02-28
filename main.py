from config.settings import TOKEN  # Зчитування токена з налаштувань
import telebot
from menu.keyboards import get_phone_keyboard  # Клавіатура для запиту телефону
from config.auth import register_auth_handlers  # Реєстрація обробників аутентифікації

# Ініціалізація бота
bot = telebot.TeleBot(TOKEN)

# Реєстрація обробників
register_auth_handlers(bot)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Вітаємо! Натисніть кнопку, щоб поділитися номером телефону:",
        reply_markup=get_phone_keyboard()
    )

# Запуск бота
if __name__ == "__main__":
    print("Бот запущено. Очікування повідомлень...")
    bot.polling(none_stop=True)
