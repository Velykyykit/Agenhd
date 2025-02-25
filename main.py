import os
import time
import telebot
import gspread
import datetime
import requests
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText

# Telegram Bot Token
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Google Sheets Setup
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Email Setup
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

user_data = {}

# ✅ Видаляємо Webhook перед запуском polling
def remove_webhook():
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    print("✅ Webhook вимкнено!")

# ✅ Отримуємо наступний номер звернення
def get_next_ticket_number():
    records = sheet.get_all_records()
    if records:
        last_number = int(records[-1]["№"])  # Останній номер
        return last_number + 1
    return 1  # Якщо таблиця порожня

# ✅ Функція для надсилання email
def send_email(subject, body, recipient):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = recipient

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD)
            server.sendmail(EMAIL, recipient, msg.as_string())
    except Exception as e:
        print(f"❌ Помилка надсилання email: {e}")

# ✅ Початок взаємодії
@bot.message_handler(commands=["start"])
def start_conversation(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}

    bot.send_message(chat_id, "Вітаю! Введіть ваш Email:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['email'] = message.text
    bot.send_message(chat_id, "Введіть ваше Ім'я:")
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "Введіть ваше Прізвище:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]['surname'] = message.text
    bot.send_message(chat_id, "Введіть ваш телефон (Viber):")
    bot.register_next_step_handler(message, get_center)

def get_center(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.text

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Південний", "Сихів")
    bot.send_message(chat_id, "Виберіть ваш навчальний центр:", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_category)

def get_category(message):
    chat_id = message.chat.id
    user_data[chat_id]['center'] = message.text

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    categories = ["Маркетинг", "Клієнти", "Персонал", "Товари", "Фінанси", "Ремонт", "Інше"]
    keyboard.add(*categories)
    
    bot.send_message(chat_id, "Оберіть вид звернення:", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_short_desc)

def get_short_desc(message):
    chat_id = message.chat.id
    user_data[chat_id]['category'] = message.text
    bot.send_message(chat_id, "Введіть короткий опис звернення:")
    bot.register_next_step_handler(message, get_desc)

def get_desc(message):
    chat_id = message.chat.id
    user_data[chat_id]['short_desc'] = message.text
    bot.send_message(chat_id, "Прошу надати максимально деталей опис запиту:")
    bot.register_next_step_handler(message, get_urgency)

def get_urgency(message):
    chat_id = message.chat.id
    user_data[chat_id]['desc'] = message.text

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Термінове", "Середнє", "Нетермінове")
    
    bot.send_message(chat_id, "Оберіть рівень терміновості:", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]['urgency'] = message.text
    bot.send_message(chat_id, "Вкажіть дату, на коли потрібно вирішити (або натисніть 'Пропустити'):")
    bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    chat_id = message.chat.id
    user_data[chat_id]['date'] = message.text

    bot.send_message(chat_id, "Прикріпіть фото (або натисніть 'Пропустити'):")
    bot.register_next_step_handler(message, save_data)

def save_data(message):
    chat_id = message.chat.id

    # Обробка фото
    photo_url = ""
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

    user_data[chat_id]['photo'] = photo_url if photo_url else "Немає"

    new_ticket = [
        get_next_ticket_number(),
        datetime.datetime.now().strftime("%H:%M, %d.%m.%Y"),
        user_data[chat_id]['email'],
        user_data[chat_id]['name'],
        user_data[chat_id]['surname'],
        user_data[chat_id]['phone'],
        user_data[chat_id]['center'],
        user_data[chat_id]['category'],
        user_data[chat_id]['short_desc'],
        user_data[chat_id]['desc'],
        user_data[chat_id]['urgency'],
        user_data[chat_id]['date'],
        user_data[chat_id]['photo']
    ]

    try:
        sheet.append_row(new_ticket)
        bot.send_message(chat_id, "✅ Ваше звернення збережено!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Помилка запису в таблицю: {e}")

    del user_data[chat_id]

# ✅ Запуск polling без помилок Render
if __name__ == "__main__":
    remove_webhook()  # Гарантовано вимикаємо Webhook

    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Помилка: {e}")
            time.sleep(5)
