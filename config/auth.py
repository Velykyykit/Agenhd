import os
import json
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

        # Визначаємо шлях до файлу у Railway
        CREDENTIALS_PATH = os.path.join("/app", self.credentials_file)

        # Логування для перевірки шляху до JSON-файлу
        print(f"DEBUG: Використовується CREDENTIALS_FILE: {CREDENTIALS_PATH}")

        # Варіант 1: Якщо файл існує в кореневій папці, використовуємо його
        if os.path.exists(CREDENTIALS_PATH):
            print("✅ JSON-файл знайдено. Використовується файл для аутентифікації.")
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, self.get_scope())
        
        # Варіант 2: Якщо `CREDENTIALS_FILE` передається як JSON-рядок
        else:
            print("⚠️ JSON-файл не знайдено. Пробуємо використати змінну середовища.")
            try:
                creds_json = json.loads(self.credentials_file)
                self.creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, self.get_scope())
            except json.JSONDecodeError as e:
                raise ValueError(f"❌ Помилка розбору JSON у CREDENTIALS_FILE: {e}")

        # Авторизація в Google Sheets
        self.client = gspread.authorize(self.creds)

        # Відкриваємо аркуш "contact"
        try:
            self.sheet = self.client.open_by_key(self.sheet_id).worksheet("contact")
            print("✅ Успішно відкрито аркуш 'contact'.")
        except gspread.exceptions.SpreadsheetNotFound:
            raise ValueError(f"❌ Помилка: Таблиця з ID {self.sheet_id} не знайдена!")

    def get_scope(self):
        """Повертає список дозволених API-скоупів."""
        return [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

    def check_user_in_database(self, phone_number):
        """
        Перевіряє, чи є номер телефону у базі Google Sheets.
        Повертає лише ім'я користувача, якщо знайдено.
        """
        try:
            phone_numbers = self.sheet.col_values(2)  # Отримуємо всі значення з другого стовпця
            if phone_number in phone_numbers:
                row_index = phone_numbers.index(phone_number) + 1
                found_data = self.sheet.row_values(row_index)  # Отримуємо весь рядок
                user_name = found_data[2] if len(found_data) > 2 else "Невідомий користувач"
                return user_name
        except Exception as e:
            print(f"❌ ПОМИЛКА при доступі до Google Sheets: {e}")
        return None  # Якщо номер не знайдено або сталася помилка
