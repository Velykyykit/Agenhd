import telebot
from keyboards import phone_number_keyboard

TOKEN = "your_telegram_bot_token"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Вітаємо! Натисніть кнопку, щоб поділитися номером телефону:",
        reply_markup=phone_number_keyboard()
    )

bot.polling(none_stop=True)

