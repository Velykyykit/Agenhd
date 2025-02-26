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
sheet_crm = client.open_by_key(SHEET_ID).worksheet("CRM")
sheet_base = client.open_by_key(SHEET_ID).worksheet("base")

# Словник для тимчасового зберігання введених даних користувача
user_data = {}

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Введіть ваш номер телефону у форматі +380...")
    bot.register_next_step_handler(message, verify_phone)

def verify_phone(message):
    phone = "'" + message.text.strip()  # Додаємо ' перед номером
    found = None
    
    base_data = sheet_base.get_all_records()
    for row in base_data:
        if row['телефон'] == phone:
            found = row
            break
    
    if not found:
        bot.send_message(message.chat.id, "Вибачте, телефон не знайдено, зверніться до адміністратора")
        return
    
    user_data[message.chat.id]["name"] = found["name"]
    user_data[message.chat.id]["phone"] = message.text.strip()
    user_data[message.chat.id]["email"] = found["email"]
    user_data[message.chat.id]["responsibility"] = found["відповідальність"]
    
    bot.send_message(message.chat.id, f"Вітаю, {found['name']}! Оберіть вид звернення:")
    markup = InlineKeyboardMarkup()
    categories = ["Маркетинг", "Клієнти", "Персонал", "Товари", "Фінанси", "Ремонт", "Інше"]
    for category in categories:
        markup.add(InlineKeyboardButton(category, callback_data=category))
    bot.send_message(message.chat.id, "Оберіть вид звернення:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = call.message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if call.data in ["Маркетинг", "Клієнти", "Персонал", "Товари", "Фінанси", "Ремонт", "Інше"]:
        user_data[user_id]["category"] = call.data
        bot.send_message(user_id, "Введіть короткий опис звернення:")
        bot.register_next_step_handler(call.message, get_short_desc)
    elif call.data in ["Термінове", "Середнє", "Нетермінове"]:
        user_data[user_id]["urgency"] = call.data
        bot.send_message(user_id, "Прикріпіть фото або введіть '-' якщо фото не потрібно")
        bot.register_next_step_handler(call.message, get_photo)

def get_short_desc(message):
    user_data[message.chat.id]["short_desc"] = message.text
    bot.send_message(message.chat.id, "Опишіть ваше звернення детальніше:")
    bot.register_next_step_handler(message, get_description)

def get_description(message):
    user_data[message.chat.id]["description"] = message.text
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Термінове", callback_data="Термінове"))
    markup.add(InlineKeyboardButton("Середнє", callback_data="Середнє"))
    markup.add(InlineKeyboardButton("Нетермінове", callback_data="Нетермінове"))
    bot.send_message(message.chat.id, "Оберіть рівень терміновості:", reply_markup=markup)

def get_photo(message):
    user_data[message.chat.id]["photo"] = message.text if message.text else "-"
    save_to_google_sheets(message.chat.id)

def save_to_google_sheets(user_id):
    data = user_data.get(user_id, {})
    last_row = len(sheet_crm.get_all_values())
    new_number = last_row + 1
    row = [
        new_number,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("name", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("category", ""),
        data.get("short_desc", ""),
        data.get("description", ""),
        data.get("urgency", ""),
        data.get("photo", ""),
        data.get("responsibility", ""),
        "В обробці",
        ""
    ]
    sheet_crm.append_row(row)
    bot.send_message(user_id, "✅ Ваше звернення прийнято та передано відповідальній особі!")

bot.polling()
