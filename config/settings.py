import os
import json

# Читаємо змінну середовища (містить JSON-ключ сервісного акаунту Google)
GOOGLE_CREDENTIALS_JSON = os.getenv("CREDENTIALS_FILE")

# Шлях до тимчасового файлу з обліковими даними Google
CREDENTIALS_FILE_PATH = "/tmp/credentials.json"

# Якщо змінна середовища існує, зберігаємо її у файл
if GOOGLE_CREDENTIALS_JSON:
    with open(CREDENTIALS_FILE_PATH, "w") as f:
        f.write(GOOGLE_CREDENTIALS_JSON)

# Конфігураційні змінні
CREDENTIALS_FILE = CREDENTIALS_FILE_PATH
SHEET_ID = os.getenv("SHEET_ID")
TOKEN = os.getenv("TOKEN")

# Загальні налаштування
BOT_NAME = "Telegram Support Bot"
TIMEOUT = 10  # Таймаут очікування дій користувача

# Ліміти
MAX_MESSAGE_LENGTH = 4096  # Максимальна довжина повідомлення
MAX_FILE_SIZE_MB = 10  # Максимальний розмір файлу, який бот може обробити

# Локалізація
DEFAULT_LANGUAGE = "uk"  # Мова за замовчуванням

# API Налаштування для Google Sheets
GOOGLE_SHEETS_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

