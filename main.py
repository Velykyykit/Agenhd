import os
import telebot
from menu.keyboards import get_phone_keyboard  
from config.auth import AuthManager  # Імпортуємо клас аутентифікації

# Отримуємо змінні з Railway
TOKEN = os.getenv("TOKEN")  
SHEET_ID = os.getenv("SHEET_ID")  
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")  # Має бути просто ім'я файлу

# Перевірка змінних середовища
if not TOKEN:
    raise ValueError("❌ TOKEN не знайдено! Перевірте змінні Railway.")
if not SHEET_ID:
    raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
if not CREDENTIALS_FILE:
    raise ValueError("❌ CREDENTIALS_FILE не знайдено! Перевірте змінні Railway.")

# Ініціалізація бота
bot = telebot.TeleBot(TOKEN)

# Перевіряємо доступ до Google Sheets перед ініціалізацією `auth.py`
try:
    auth_manager = AuthManager(SHEET_ID, CREDENTIALS_FILE)
    print("✅ Успішно підключено до Google Sheets!")
except Exception as e:
    print(f"❌ ПОМИЛКА: Не вдалося підключитися до Google Sheets: {e}")
    exit(1)  # Завершуємо програму, якщо не вдалося підключитися

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Запит на надання номера телефону для аутентифікації після команди /start."""
    markup = get_phone_keyboard()
    
    bot.send_message(
        message.chat.id,
        "Поділіться номером для аутентифікації:",  
        reply_markup=markup  
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Обробляє отримання номера телефону від користувача та перевіряє його в базі даних."""
    if message.contact:
        phone_number = message.contact.phone_number

        # Використовуємо AuthManager для перевірки номера
        try:
            user_name = auth_manager.check_user_in_database(phone_number)

            if user_name:
                bot.send_message(
                    message.chat.id,
                    f"✅ Вітаю, *{user_name}*! Ви успішно ідентифіковані. 🎉",
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(
                    message.chat.id,
                    "❌ Ваш номер не знайдено у базі. Зверніться до адміністратора."
                )
        except Exception as e:
            bot.send_message(
                message.chat.id,
                "❌ Сталася помилка під час перевірки номера. Спробуйте пізніше."
            )
            print(f"❌ ПОМИЛКА під час перевірки номера: {e}")

if __name__ == "__main__":
    print("✅ Бот запущено. Очікування повідомлень...")
    bot.polling(none_stop=True)
