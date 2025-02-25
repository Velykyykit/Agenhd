import os
import time
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz

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

    # Отримуємо останній номер звернення
    records = sheet.get_all_records()
    last_number = records[-1]['№'] if records else 0
    user_data[chat_id]['number'] = last_number + 1

    bot.send_message(chat_id, "Вітаю! Введіть ваш email:")
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
    bot.send_message(chat_id, "Введіть ваш номер телефону:")
    bot.register_next_step_handler(message, get_center)

def get_center(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.text

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Південний", "Сихів")
    bot.send_message(chat_id, "Виберіть ваш навчальний центр:", reply_markup=markup)
    bot.register_next_step_handler(message, get_category)

def get_category(message):
    chat_id = message.chat.id
    user_data[chat_id]['center'] = message.text

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    categories = ["Маркетинг", "Клієнти", "Персонал", "Товари", "Фінанси", "Ремонт", "Інше"]
    markup.add(*categories)
    bot.send_message(chat_id, "Оберіть вид звернення:", reply_markup=markup)
    bot.register_next_step_handler(message, get_short_desc)

def get_short_desc(message):
    chat_id = message.chat.id
    user_data[chat_id]['category'] = message.text

    examples = {
        "Маркетинг": "Наприклад: Потрібна рекламна кампанія",
        "Клієнти": "Наприклад: Скарга від батьків",
        "Персонал": "Наприклад: Запит на навчання",
        "Товари": "Наприклад: Закінчилися підручники",
        "Фінанси": "Наприклад: Помилка у фінансовому звіті",
        "Ремонт": "Наприклад: Поломка ноутбука",
        "Інше": "Наприклад: Потрібна консультація"
    }

    bot.send_message(chat_id, f"{examples[user_data[chat_id]['category']]} Введіть ваш короткий опис:")
    bot.register_next_step_handler(message, get_desc)

def get_desc(message):
    chat_id = message.chat.id
    user_data[chat_id]['short_desc'] = message.text
    bot.send_message(chat_id, "Прошу надати максимально детальний опис запиту:")
    bot.register_next_step_handler(message, get_urgency)

def get_urgency(message):
    chat_id = message.chat.id
    user_data[chat_id]['desc'] = message.text

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("Термінове", "Середнє", "Нетермінове", "Ввести дату вручну")
    bot.send_message(chat_id, "Виберіть терміновість або введіть дату:", reply_markup=markup)
    bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    chat_id = message.chat.id
    user_data[chat_id]['urgency'] = message.text if message.text not in ["Термінове", "Середнє", "Нетермінове"] else message.text
    bot.send_message(chat_id, "Якщо бажаєте додати фото, надішліть його зараз або пропустіть цей крок.")
    bot.register_next_step_handler(message, save_data)

def save_data(message):
    chat_id = message.chat.id

    user_data[chat_id]['photo'] = message.photo[-1].file_id if message.photo else ""

    ua_time = datetime.now(pytz.timezone('Europe/Kiev')).strftime("%H:%M, %d.%m.%Y")
    user_data[chat_id]['date'] = ua_time

    sheet.append_row([user_data[chat_id][key] for key in ['number', 'date', 'email', 'name', 'surname', 'phone', 'center', 'category', 'short_desc', 'desc', 'urgency', 'photo']])

    bot.send_message(chat_id, "✅ Ваше звернення збережене!")
    del user_data[chat_id]

while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Помилка: {e}")
        time.sleep(5)
