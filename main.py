import telebot
import os
from menu.keyboards import get_phone_keyboard  # Імпортуємо клавіатуру для запиту телефону

# Отримуємо токен з змінної середовища
TOKEN = os.getenv("TOKEN")  
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Запит на надання номера телефону без привітання."""
    # Використовуємо функцію get_phone_keyboard() для запиту тільки номера телефону
    markup = get_phone_keyboard()  # Використовуємо тільки одну кнопку

    bot.send_message(
        message.chat.id,
        "Натисніть кнопку, щоб поділитися своїм номером телефону.",  # Текст без привітання
        reply_markup=markup  # Відправляється тільки одна кнопка
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
