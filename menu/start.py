import telebot
import os
from keyboards import phone_number_keyboard

# Отримання токену з змінної середовища
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Вітаємо! Натисніть кнопку, щоб поділитися номером телефону:",
        reply_markup=phone_number_keyboard()
    )

bot.polling(none_stop=True)
