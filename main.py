import telebot
import os
from menu.keyboards import get_phone_keyboard  # Імпортуємо клавіатуру для запиту телефону

# Отримуємо токен з змінної середовища
TOKEN = os.getenv("TOKEN")  
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Привітання після команди /start та запит на надання номера телефону."""
    # Використовуємо функцію get_phone_keyboard() з menu/keyboards.py
    markup = get_phone_keyboard()

    bot.send_message(
        message.chat.id,
        "Привіт! Я бот. Натисніть кнопку, щоб поділитися своїм номером телефону.",
        reply_markup=markup
    )

# Обробник отриманого контакту
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Обробляє отримання номера телефону від користувача."""
    if message.contact:
        phone_number = message.contact.phone_number
        bot.send_message(
            message.chat.id,
            f"Дякую за надання номера телефону: {phone_number}"
        )

# Запуск бота
if __name__ == "__main__":
    print("Бот запущено. Очікування повідомлень...")
    bot.polling(none_stop=True)
