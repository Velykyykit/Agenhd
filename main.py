import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
import datetime
import os

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

# Відповідальні особи за зверненнями
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

# Отримуємо наступний номер звернення
def get_next_ticket_number():
    records = sheet.get_all_records()
    return int(records[-1]["№"]) + 1 if records else 1

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Вітаю! Надішліть ваше звернення у форматі:")
    bot.send_message(message.chat.id, "Ім'я Прізвище\nТелефон\nНавчальний центр\nВид звернення\nКороткий опис\nОпис\nТерміновість\nДата подання")

@bot.message_handler(content_types=["text", "photo"])
def handle_message(message):
    try:
        chat_id = message.chat.id

        if message.photo:  # Якщо користувач надіслав фото
            file_info = bot.get_file(message.photo[-1].file_id)
            photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        else:
            photo_url = "Немає"

        data = message.text.split("\n")
        if len(data) < 8:
            bot.reply_to(message, "Будь ласка, введіть всі необхідні поля!")
            return

        name, phone, center, category, short_desc, desc, urgency, date = data[:8]

        if category not in RESPONSIBLES:
            bot.reply_to(message, "Невідома категорія звернення. Виберіть правильну категорію!")
            return

        responsible = RESPONSIBLES[category]
        resp_name, resp_phone, resp_email = responsible["name"], responsible["phone"], responsible["email"]

        new_ticket = [
            get_next_ticket_number(),
            datetime.datetime.now().strftime("%H:%M, %d.%m.%Y"),  # Додаємо поточну дату в українському форматі
            name,
            phone,
            center,
            category,
            short_desc,
            desc,
            urgency,
            date,
            photo_url,  # Додаємо фото
            resp_name,
            resp_phone,
            "В обробці"
        ]

        sheet.append_row(new_ticket)

        email_body = f"Нове звернення:\nІм'я: {name}\nТелефон: {phone}\nНавчальний центр: {center}\nКатегорія: {category}\nОпис: {desc}\nТерміновість: {urgency}\nФото: {photo_url}"
        send_email("Нове звернення", email_body, resp_email)
        send_email("Нове звернення", email_body, "gammmerx@gmail.com")

        bot.reply_to(message, f"✅ Ваше звернення передано відповідальному: {resp_name} ({resp_phone}). Ви отримаєте оновлення щодо статусу!")
    
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {e}")

bot.polling()
