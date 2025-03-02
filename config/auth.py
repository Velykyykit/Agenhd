import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class AuthManager:
    def __init__(self, sheet_id, credentials_file):
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.cache = {}  # Додаємо кеш

        if not self.sheet_id:
            raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
        if not self.credentials_file:
            raise ValueError("❌ CREDENTIALS_FILE не знайдено! Перевірте змінні Railway.")

        # Використовуємо абсолютний шлях, щоб знайти файл у кореневій папці
        CREDENTIALS_PATH = os.path.join("/app", self.credentials_file)

        # Виводимо шлях до файлу в логах (щоб перевірити)
        print(f"DEBUG: Використовується CREDENTIALS_FILE: {CREDENTIALS_PATH}")

        # Перевіряємо, чи існує файл
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(f"❌ Файл облікових даних не знайдено: {CREDENTIALS_PATH}")

        # Авторизація в Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
        self.client = gspread.authorize(self.creds)

        # Відкриваємо аркуш "contact"
        self.sheet = self.client.open_by_key(self.sheet_id).worksheet("contact")

    def clean_phone_number(self, phone):
        """Видаляє всі пробіли, дужки, тире та інші зайві символи з номера телефону."""
        phone = re.sub(r"[^\\d+]", "", phone)  # Видаляємо все, крім цифр та знака "+"
        if not phone.startswith("+"):
            phone = f"+{phone}"  # Додаємо "+" на початок, якщо його немає
        return phone

    def check_user_in_database(self, phone_number):
        """
        Перевіряє, чи є номер телефону у базі Google Sheets.
        Повертає словник з ID, ім'ям, email та роллю, якщо знайдено.
        Використовує кеш для зменшення запитів до Google Sheets.
        """
        phone_number = self.clean_phone_number(phone_number)

        # Якщо номер уже в кеші, повертаємо дані з кешу
        if phone_number in self.cache:
            print(f"DEBUG: Взято з кешу -> {self.cache[phone_number]}")
            return self.cache[phone_number]

        # Отримуємо всі значення з таблиці
        all_data = self.sheet.get_all_values()

        # Фільтруємо лише ті рядки, де є номер телефону
        valid_rows = [row for row in all_data[1:] if len(row) > 1 and row[1].strip()]

        # Витягуємо тільки чисті номери телефонів
        phone_numbers = [self.clean_phone_number(row[1].strip()) for row in valid_rows]

        print(f"DEBUG: Отримано номер: {phone_number}")
        print(f"DEBUG: Номери в базі (після очищення): {phone_numbers}")

        if phone_number in phone_numbers:
            row_index = phone_numbers.index(phone_number)  # Знаходимо правильний індекс
            found_data = valid_rows[row_index]  # Беремо відповідний рядок

            print(f"DEBUG: Знайдено рядок у таблиці: {found_data}")

            # Отримуємо дані: ID (1-й стовпець), ім'я (2-й стовпець), email (3-й стовпець), роль (7-й стовпець)
            user_data = {
                "id": found_data[0].strip() if len(found_data) > 0 else "Невідомий ID",
                "name": found_data[1].strip() if len(found_data) > 1 else "Невідоме ім'я",
                "email": found_data[2].strip() if len(found_data) > 2 else "Невідомий email",
                "role": found_data[6].strip() if len(found_data) > 6 else "Невідома роль"
            }

            # Зберігаємо у кеш
            self.cache[phone_number] = user_data

            return user_data  # Повертаємо словник

        return None
