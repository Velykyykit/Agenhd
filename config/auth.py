import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config.credentials import SHEET_ID

# Підключення до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet("contact")  # Відкриваємо аркуш "contact"

def check_user_in_database(phone_number):
    """
    Перевіряє наявність номера телефону у базі даних Google Sheets.
    Повертає ім'я користувача та навчальний центр, якщо знайдено.
    """
    # Отримуємо всі значення з другого стовпця
    phone_numbers = sheet.col_values(2)  # другий стовпець (де зберігаються номери)

    # Пошук номера телефону у списку
    if phone_number in phone_numbers:
        row_index = phone_numbers.index(phone_number) + 1
        found_data = sheet.row_values(row_index)

        user_name = found_data[2] if len(found_data) > 2 else "Вас немає у базі, зверніться до адміністратора"

        
        return user_name, center
    return None, None
