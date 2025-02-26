import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
import datetime

# Telegram Bot Token
TOKEN = "7868393223:AAGw_x1U3r2MU9gQyfqL2kg4vtM7oy8jiUI"
bot = telebot.TeleBot(TOKEN)

# Google Sheets Setup
SHEET_ID = "1LO5YVAQBO872YpbUb-DbIWgL4W9ybOY6g04Cr-nqJCk"
CREDENTIALS_FILE = "zvernennya-42124e812469.json"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Email Setup
EMAIL = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"
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
    bot.reply_to(message, "Вітаю! Надішліть ваше звернення у форматі:")
    bot.send_message(message.chat.id, "Ім'я Прізвище\nТелефон\nНавчальний центр\nВид звернення\nКороткий опис\nОпис\nТерміновість\nДата подання")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
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
        
        sheet.append_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message.chat.id, name, phone, center, category, short_desc, desc, urgency, "", resp_name, resp_phone, "В обробці"])
        
        email_body = f"Нове звернення від {name}:\n{short_desc}\n{desc}\nТерміновість: {urgency}\nКонтакт: {phone}\nНавчальний центр: {center}"
        send_email("Нове звернення", email_body, resp_email)
        send_email("Нове звернення", email_body, "gammmerx@gmail.com")
        
        bot.reply_to(message, f"Ваше звернення передано відповідальному: {resp_name} ({resp_phone}). Ви отримаєте оновлення щодо статусу!")
    except Exception as e:
        bot.reply_to(message, f"Помилка: {e}")

bot.polling()
