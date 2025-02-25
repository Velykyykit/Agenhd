import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText

# Telegram Bot Token
TOKEN = "7868393223:AAGw_x1U3r2MU9gQyfqL2kg4vtM7oy8jiUI"
bot = telebot.TeleBot(TOKEN)

# Google Sheets Setup
SHEET_ID = "1LO5YVAQBO872YpbUb-DbIWgL4W9ybOY6g04Cr-nqJCk"
CREDENTIALS_FILE = "zvernennya-42124e812469.json"  # Файл із ключами для доступу до Google Sheets

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Email Setup
EMAIL = "gammmerx@gmail.com"
EMAIL_PASSWORD = "sendox321"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(subject, body, recipient):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = recipient
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, recipient, msg.as_string())

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
    user_data[chat_id]['center'] = message.text
    bot.send_message(chat_id, "Оберіть вид звернення (Маркетинг, Клієнти, Персонал, Товари, Фінанси, Ремонт, Інше):")
    bot.register_next_step_handler(message, get_short_desc)

def get_short_desc(message):
    chat_id = message.chat.id
    user_data[chat_id]['category'] = message.text
    bot.send_message(chat_id, "Короткий опис звернення:")
    bot.register_next_step_handler(message, get_desc)

def get_desc(message):
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
    
    sheet.append_row([data['name'], data['phone'], data['center'], data['category'], data['short_desc'], data['desc'], data['urgency'], data['date'], responsible])
    
    # Надсилання email
    email_body = f"Нове звернення:\n{data['name']}\n{data['phone']}\n{data['center']}\n{data['category']}\n{data['short_desc']}\n{data['desc']}\n{data['urgency']}\n{data['date']}"
    send_email("Нове звернення", email_body, "gammmerx@gmail.com")
    
    bot.send_message(chat_id, "Ваше звернення збережене та передане відповідальним!")
    del user_data[chat_id]

bot.polling()
