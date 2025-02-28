import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Отримуємо змінні з Railway
SHEET_ID = os.getenv("SHEET_ID")  
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")  

# Перевірка змінних
if not SHEET_ID:
    raise ValueError("❌ Помилка: SHEET_ID не знайдено! Перевірте налаштування Railway.")
if not CREDENTIALS_FILE:
    raise ValueError("❌ Помилка: CREDENTIALS_FILE не знайдено! Перевірте налаштування Railway.")

# Авторизація в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(CREDENTIALS_FILE)  # Розбираємо JSON з змінної
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)

# Відкриваємо аркуш "contact"
sheet = client.open_by_key(SHEET_ID).worksheet("contact")

def check_user_in_database(phone_number):
    """
    Перевіряє, чи є номер телефону у базі Google Sheets.
    Повертає лише ім'я користувача, якщо знайдено.
    """
    # Отримуємо всі значення з другого стовпця (номери телефонів)
    phone_numbers = sheet.col_values(2)  

    # Пошук номера телефону у списку
    if phone_number in phone_numbers:
        row_index = phone_numbers.index(phone_number) + 1
        found_data = sheet.row_values(row_index)  # Отримуємо весь рядок

        # Отримуємо ім'я користувача з 3-го стовпця (змінюй індекс за потреби)
        user_name = found_data[2] if len(found_data) > 2 else "Невідомий користувач"

        return user_name  # Повертаємо лише ім'я

    return None  # Якщо номер не знайдено
