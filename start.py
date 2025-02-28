### start.py (Обробка команди /start та аутентифікація користувача)
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from bot.services.google_sheets import check_user_phone
from bot.keyboards import phone_keyboard

# Функція для обробки старту бота та авторизації
def register_start_handler(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message: Message):
        bot.send_message(message.chat.id, "Привіт! Будь ласка, поділіться своїм номером телефону для авторизації.", reply_markup=phone_keyboard())

    @bot.message_handler(content_types=['contact'])
    def handle_contact(message: Message):
        phone_number = message.contact.phone_number
        if check_user_phone(phone_number):
            bot.send_message(message.chat.id, "✅ Ваш номер знайдено у базі! Ви успішно авторизувалися.")
        else:
            bot.send_message(message.chat.id, "❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")
