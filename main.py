import telebot
import os

# Отримуємо токен з змінної середовища
TOKEN = os.getenv("TOKEN")  
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Привітання після команди /start."""
    bot.send_message(message.chat.id, "Привіт! Я бот.")

# Запуск бота
if __name__ == "__main__":
    print("Бот запущено. Очікування повідомлень...")
    bot.polling(none_stop=True)
