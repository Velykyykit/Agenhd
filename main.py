import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Telegram Bot Token
TOKEN = os.getenv("TOKEN")  # Використовуємо змінну середовища
bot = telebot.TeleBot(TOKEN)

# Google Sheets Setup
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet_base = client.open_by_key(SHEET_ID).worksheet("base")

# Словник для тимчасового зберігання введених даних користувача
user_data = {}

@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Стартова команда: запитуємо номер телефону"""
    user_data[message.chat.id] = {}

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📱 Надіслати мій номер", request_contact=True)
    markup.add(button)

    bot.send_message(message.chat.id, "Будь ласка, надішліть свій номер телефону для ідентифікації:", reply_markup=markup)

@bot.message_handler(content_types=["contact"])
def verify_phone(message):
    """Перевіряємо телефонний номер у базі"""
    if message.contact is None:
        bot.send_message(message.chat.id, "❌ Ви не надали номер телефону. Спробуйте ще раз.")
        return

    phone = message.contact.phone_number.strip()
    if not phone.startswith("+"):
        phone = "+" + phone  # Додаємо "+" якщо немає

    base_data = sheet_base.get_all_values()
    phones_column = [row[1].strip().lstrip("'") for row in base_data[1:]]  # Телефони у 2-й колонці

    if phone in phones_column:
        row_index = phones_column.index(phone) + 1
        found_data = sheet_base.row_values(row_index + 1)

        user_data[message.chat.id] = {
            "name": found_data[2],  # Ім'я у колонці C
            "phone": phone,
            "email": found_data[3],  # Email у колонці D
            "responsibility": found_data[5]  # Відповідальність у колонці F
        }

        bot.send_message(
            message.chat.id, 
            f"✅ Вітаю, {found_data[2]}! Ваш номер знайдено у базі. Ви підтверджуєте, що це ваш номер?"
        )
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("✅ Так"), KeyboardButton("❌ Ні"))
        bot.send_message(message.chat.id, "Виберіть:", reply_markup=markup)
        bot.register_next_step_handler(message, confirm_phone)
    else:
        bot.send_message(message.chat.id, "❌ Ваш номер телефону не знайдено у базі. Зверніться до адміністратора.")

def confirm_phone(message):
    """Користувач підтверджує чи відхиляє номер телефону"""
    if message.text == "✅ Так":
        bot.send_message(message.chat.id, "✅ Дякую! Ви успішно ідентифіковані.")
        # Тут можна перейти до наступного кроку
    else:
        bot.send_message(message.chat.id, "❌ Ви відхилили номер. Спробуйте ще раз або зверніться до адміністратора.")

bot.polling()
