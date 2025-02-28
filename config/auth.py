import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AuthManager:
    def __init__(self, sheet_id, credentials_file):
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file

        if not self.sheet_id:
            raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
        if not self.credentials_file:
            raise ValueError("❌ CREDENTIALS_FILE не знайдено! Перевірте змінні Railway.")

        # Визначаємо шлях до файлу у кореневій папці
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
        CREDENTIALS_PATH = os.path.join(BASE_DIR, self.credentials_file)

        # Виводимо шлях до файлу в логах (щоб перевірити)
        print(f"DEBUG: Використовується CREDENTIALS_FILE: {CREDENTIALS_PATH}")

        # Авторизація в Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
        self.client = gspread.authorize(self.creds)

        # Відкриваємо аркуш "contact"
        self.sheet = self.client.open_by_key(self.sheet_id).worksheet("contact")

    def check_user_in_database(self, phone_number):
        """
        Перевіряє, чи є номер телефону у базі Google Sheets.
        Повертає лише ім'я користувача, якщо знайдено.
        """
        phone_numbers = self.sheet.col_values(2)  # Отримуємо всі значення з другого стовпця

        if phone_number in phone_numbers:
            row_index = phone_numbers.index(phone_number) + 1
            found_data = self.sheet.row_values(row_index)  # Отримуємо весь рядок

            # Отримуємо ім'я користувача з 3-го стовпця (змінюй індекс за потреби)
            user_name = found_data[2] if len(found_data) > 2 else "Невідомий користувач"

            return user_name  # Повертаємо лише ім'я

        return None  # Якщо номер не знайдено
