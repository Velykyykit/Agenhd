import telebot
import gspread
import datetime
import os
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText

# Налаштування змінних оточення
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

bot = telebot.TeleBot(TOKEN)

# Web сервер на Flask
app = Flask(__name__)

# Google Sheets авторизація
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Відповідальні особи
RESPONSIBLES = {
    "Маркетинг": {"name": "Іван Іванов", "phone": "+380671234567", "email": "marketing@example.com"},
    "Клієнти": {"name": "Петро Петренко", "phone": "+380632345678", "email": "clients@example.com"},
    "Персонал": {"name": "Олена Олененко", "phone": "+380501234567", "email": "hr@example.com"},
    "Товари": {"name": "Василь Василенко", "phone": "+380931234567", "email": "products@example.com"},
    "Фінанси": {"name": "Анна Анненко", "phone": "+380671234890", "email": "finance@example.com"},
    "Ремонт": {"name": "Микола Миколенко", "phone": "+380662345678", "email": "repair@example.com"},
    "Інше": {"name": "Олександр Олександров", "phone": "+380731234567", "email": "other@example.com"}
}

# Функція для надсилання email
def send_email(subject, body, recipient):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = recipient
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, recipient, msg.as_string())

# Функція отримання наступного номера звернення
def get_next_ticket_number():
    records = sheet.get_all_records()
    return int(records[-1]["№"]) + 1 if records else 1

# Покрокове заповнення форми
user_data = {}

@bot.message_handler(commands=["start"])
def start_conversation(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}

    bot.send_message(chat_id, "Вітаю! Введіть ваше Ім'я та Прізвище:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text

    bot.send_message(chat_id, "Введіть ваш номер телефону (Viber):")
    bot.register_next_step_handler(message, get_center)

def get_center(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.text

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Південний", "Сихів")
    bot.send_message(chat_id, "Виберіть навчальний центр:", reply_markup=keyboard)
    bot.register_next_step_handler(message, get_category)

def get_category(message):
    chat_id = message.chat.id
    user_data[chat_id]['center'] = message.text

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    categories = list(RESPONSIBLES.keys())
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
    bot.register_next_step_handler(message, save_data)

def save_data(message):
    chat_id = message.chat.id
    user_data[chat_id]['date'] = message.text

    responsible = RESPONSIBLES[user_data[chat_id]['category']]
    
    new_ticket = [
        get_next_ticket_number(),
        datetime.datetime.now().strftime("%H:%M, %d.%m.%Y"),
        user_data[chat_id]['name'],
        user_data[chat_id]['phone'],
        user_data[chat_id]['center'],
        user_data[chat_id]['category'],
        user_data[chat_id]['short_desc'],
        user_data[chat_id]['desc'],
        user_data[chat_id]['urgency'],
        user_data[chat_id]['date'],
        responsible["name"],
        responsible["phone"],
        "В обробці"
    ]

    sheet.append_row(new_ticket)

    bot.send_message(chat_id, f"✅ Ваше звернення передано {responsible['name']} ({responsible['phone']})")

    del user_data[chat_id]

# Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

# Запуск Webhook
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=5000, debug=True)
