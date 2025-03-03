import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AuthManager:
    def __init__(self, sheet_id, credentials_file):
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.cache = {}

        if not self.sheet_id:
            raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
        if not self.credentials_file:
            raise ValueError("❌ CREDENTIALS_FILE не знайдено! Перевірте змінні Railway.")

        CREDENTIALS_PATH = os.path.join("/app", self.credentials_file)
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(f"❌ Файл облікових даних не знайдено: {CREDENTIALS_PATH}")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.sheet_id).worksheet("contact")  # Назва аркуша "contact"

    def clean_phone_number(self, phone):
        """Очищення номера телефону, зберігаючи коректний формат."""
        phone = re.sub(r"[^\d+]", "", phone)  # Видаляємо всі символи, крім цифр і "+"
        if not phone.startswith("+"):
            phone = f"+{phone}"
        if len(phone) < 10:  # Якщо номер занадто короткий – можливо, це помилка
            return None
        return phone

    def check_user_in_database(self, phone_number):
        """Перевіряє наявність номера у базі та повертає ID, ім'я, email, роль."""
        phone_number = self.clean_phone_number(phone_number)
        if not phone_number:
            print("❌ ПОМИЛКА: Невірний формат номера телефону.")
            return None

        # Якщо номер є у кеші, повертаємо дані з кешу
        if phone_number in self.cache:
            print(f"DEBUG: Взято з кешу -> {self.cache[phone_number]}")
            return self.cache[phone_number]

        # Отримуємо всі значення з таблиці
        all_data = self.sheet.get_all_values()

        # Проходимо по всіх рядках, шукаємо номер у 2-му стовпці (телефон)
        for row in all_data[1:]:  # Пропускаємо заголовок
            if len(row) > 1:  # Переконуємося, що рядок не пустий
                stored_phone = self.clean_phone_number(row[1].strip())  # Отримуємо телефон
                if stored_phone == phone_number:
                    print(f"DEBUG: Знайдено рядок у таблиці: {row}")

                    # Формуємо відповідь
                    user_data = {
                        "id": row[0].strip() if len(row) > 0 else "Невідомий ID",  # ID (A)
                        "name": row[2].strip() if len(row) > 2 else "Невідоме ім'я",  # Name (C)
                        "email": row[3].strip() if len(row) > 3 else "Невідомий email",  # Email (D)
                        "role": row[6].strip() if len(row) > 6 else "Невідома роль"  # Role (G)
                    }

                    # Додаємо у кеш
                    self.cache[phone_number] = user_data

                    return user_data

        return None
