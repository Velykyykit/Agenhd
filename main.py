import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
import datetime
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Bot Token
TOKEN = os.getenv("TOKEN")  # Використовуємо змінну середовища
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

# Словник для тимчасового зберігання введених даних користувача
user_data = {}

def send_email(subject, body, recipient):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = recipient
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, recipient, msg.as_string())

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Вітаю! Введіть ваше Ім'я та Прізвище:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Введіть ваш номер телефону (Viber):")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_data[message.chat.id]["phone"] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Південний", callback_data="Південний"))
    markup.add(InlineKeyboardButton("Сихів", callback_data="Сихів"))
    bot.send_message(message.chat.id, "Виберіть навчальний центр:", reply_markup=markup)

def get_category(message):
    user_data[message.chat.id]["center"] = message.text
    markup = InlineKeyboardMarkup()
    for category in RESPONSIBLES.keys():
        markup.add(InlineKeyboardButton(category, callback_data=category))
    bot.send_message(message.chat.id, "Оберіть вид звернення:", reply_markup=markup)

def get_short_desc(message):
    user_data[message.chat.id]["category"] = message.text
    bot.send_message(message.chat.id, "Введіть короткий опис звернення:")
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    user_data[message.chat.id]["short_desc"] = message.text
    bot.send_message(message.chat.id, "Опишіть ваше звернення детальніше:")
    bot.register_next_step_handler(message, get_urgency)

def get_urgency(message):
    user_data[message.chat.id]["description"] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Термінове", callback_data="Термінове"))
    markup.add(InlineKeyboardButton("Середнє", callback_data="Середнє"))
    markup.add(InlineKeyboardButton("Нетермінове", callback_data="Нетермінове"))
    bot.send_message(message.chat.id, "Оберіть рівень терміновості:", reply_markup=markup)

def save_to_google_sheets(user_id):
    data = user_data[user_id]
    responsible = RESPONSIBLES[data["category"]]
    row = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data["name"], data["phone"], data["center"], data["category"], 
           data["short_desc"], data["description"], data["urgency"], responsible["name"], responsible["phone"], "В обробці"]
    sheet.append_row(row)
    return responsible

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = call.message.chat.id

    if call.data in ["Південний", "Сихів"]:
        user_data[user_id]["center"] = call.data
        markup = InlineKeyboardMarkup()
        for category in RESPONSIBLES.keys():
            markup.add(InlineKeyboardButton(category, callback_data=category))
        bot.send_message(user_id, "Оберіть вид звернення:", reply_markup=markup)

    elif call.data in RESPONSIBLES.keys():
        user_data[user_id]["category"] = call.data
        bot.send_message(user_id, "Введіть короткий опис звернення:")
        bot.register_next_step_handler(call.message, get_short_desc)

    elif call.data in ["Термінове", "Середнє", "Нетермінове"]:
        user_data[user_id]["urgency"] = call.data
        responsible = save_to_google_sheets(user_id)
        bot.send_message(user_id, f"✅ Ваше звернення передано {responsible['name']} ({responsible['phone']})")
        send_email("Нове звернення", f"Звернення: {user_data[user_id]}", "gammmerx@gmail.com")

bot.polling()
