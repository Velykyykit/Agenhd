### main.py (Головний файл запуску бота)
import telebot
from bot.config import TOKEN
from bot.handlers import register_handlers
from bot.logging_service import setup_logging

# Крок 1: Налаштування логування
setup_logging()

# Крок 2: Ініціалізація бота
bot = telebot.TeleBot(TOKEN)

# Крок 3: Реєстрація всіх обробників команд
register_handlers(bot)

# Крок 4: Запуск бота
if __name__ == "__main__":
    print("Бот запущено. Очікування повідомлень...")
    bot.polling(none_stop=True)
