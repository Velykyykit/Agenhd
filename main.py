import telebot
from config.settings import TOKEN  # Виправлено шлях імпорту
from config.handlers import register_handlers  # Виправлено шлях імпорту
from config.logging_service import setup_logging  # Виправлено шлях імпорту

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
