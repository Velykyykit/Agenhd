import re
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials

class AuthManager:
    def __init__(self, sheet_id, credentials_json):
        self.sheet_id = sheet_id
        self.credentials_json = credentials_json
        self.cache = {}

        if not self.sheet_id:
            raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
        if not self.credentials_json:
            raise ValueError("❌ CREDENTIALS_JSON не знайдено! Перевірте змінні Railway.")

        # Використовуємо JSON напряму
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.credentials_json, scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.sheet_id).worksheet("contact")

    def clean_phone_number(self, phone):
        """Очищення номера телефону, зберігаючи коректний формат."""
        phone = re.sub(r"[^\d+]", "", phone)  # Видаляємо всі символи, крім цифр і "+"
        if not phone.startswith("+"):
            phone = f"+{phone}"
        if len(phone) < 10:
            return None
        return phone

    async def check_user_in_database(self, phone_number):
        """Перевіряє наявність номера у базі та повертає ID, ім'я, email, роль."""
        phone_number = self.clean_phone_number(phone_number)
        if not phone_number:
            return None

        if phone_number in self.cache:
            return self.cache[phone_number]

        all_data = await asyncio.to_thread(self.sheet.get_all_values)

        for row in all_data[1:]:
            if len(row) > 1 and self.clean_phone_number(row[1].strip()) == phone_number:
                user_data = {
                    "id": row[0].strip(),
                    "name": row[2].strip(),
                    "email": row[3].strip(),
                    "role": row[6].strip()
                }
                self.cache[phone_number] = user_data
                return user_data
        return None
