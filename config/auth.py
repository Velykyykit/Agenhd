import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Отримуємо змінні з Railway
SHEET_ID = os.getenv("SHEET_ID")  
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")  

# Перевірка змінних
if not SHEET_ID:
    raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
if not CREDENTIALS_FILE:
    raise ValueError("❌ CREDENTIALS_FILE не знайдено! Перевірте змінні Railway.")

# Визначаємо абсолютний шлях до файлу в кореневій папці
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
CREDENTIALS_PATH = os.path.join(BASE_DIR, CREDENTIALS_FILE)

# Виводимо шлях до файлу в логах (щоб перевірити)
print(f"DEBUG: Використовується CREDENTIALS_FILE: {CREDENTIALS_PATH}")

# Авторизація в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
client = gspread.authorize(creds)

# Відкриваємо аркуш "contact"
sheet = client.open_by_key(SHEET_ID).worksheet("contact")
