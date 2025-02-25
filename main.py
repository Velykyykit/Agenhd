import os
import time
import telebot
import gspread
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

# Telegram Bot Handlers
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
    bot.send_message(chat_id, "Введіть ваш номер телефону:")
    bot.register_next_step_handler(message, get_center)

def get_center(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.text
    bot.send_message(chat_id, "Виберіть ваш навчальний центр (Південний, Сихів):")
    bot.register_next_step_handler(message, get_category)

def get_category(message):
    chat_id = message.chat.id
    category = message.text.strip().lower()
    valid_categories = ["маркетинг", "клієнти", "персонал", "товари", "фінанси", "ремонт", "інше"]
    
    if category not in valid_categories:
        bot.send_message(chat_id, "⚠ Невірний вибір. Оберіть із запропонованих варіантів!")
        bot.register_next_step_handler(message, get_category)
        return

    user_data[chat_id]['category'] = category
    bot.send_message(chat_id, "Короткий опис звернення:")
    bot.register_next_step_handler(message, get_short_desc)

def get_short_desc(message):
    chat_id = message.chat.id
    user_data[chat_id]['short_desc'] = message.text
    bot.send_message(chat_id, "Детальний опис звернення:")
    bot.register_next_step_handler(message, get_urgency)

def get_urgency(message):
    chat_id = message.chat.id
    user_data[chat_id]['desc'] = message.text
    bot.send_message(chat_id, "Виберіть терміновість (Термінове, Середнє, Нетерміново):")
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    chat_id = message.chat.id
    user_data[chat_id]['urgency'] = message.text
    bot.send_message(chat_id, "Вкажіть дату подання (M/d/yyyy):")
    bot.register_next_step_handler(message, save_data)

def save_data(message):
    chat_id = message.chat.id
    user_data[chat_id]['date'] = message.text
    
    data = user_data[chat_id]
    responsible = "gammmerx@gmail.com"  # Тут можна додати логіку вибору відповідального

    try:
        sheet.append_row([data['name'], data['phone'], data['center'], data['category'], data['short_desc'], data['desc'], data['urgency'], data['date'], responsible])
    except Exception as e:
        bot.send_message(chat_id, f"❌ Помилка збереження в таблицю: {e}")
        return

    email_body = f"Нове звернення:\n{data['name']}\n{data['phone']}\n{data['center']}\n{data['category']}\n{data['short_desc']}\n{data['desc']}\n{data['urgency']}\n{data['date']}"
    send_email("Нове звернення", email_body, "gammmerx@gmail.com")

    bot.send_message(chat_id, "✅ Ваше звернення збережене та передане відповідальним!")
    del user_data[chat_id]

while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Помилка: {e}")
        time.sleep(5)
