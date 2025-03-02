import os
import telebot
from menu.keyboards import get_phone_keyboard  
from config.auth import AuthManager  # Імпортуємо клас аутентифікації

# Отримуємо змінні з Railway
TOKEN = os.getenv("TOKEN")  
SHEET_ID = os.getenv("SHEET_ID")  
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")  

# Перевіряємо, чи всі змінні встановлені
if not TOKEN:
    raise ValueError("❌ TOKEN не знайдено! Перевірте змінні Railway.")
if not SHEET_ID:
    raise ValueError("❌ SHEET_ID не знайдено! Перевірте змінні Railway.")
if not CREDENTIALS_FILE:
    raise ValueError("❌ CREDENTIALS_FILE не знайдено! Перевірте змінні Railway.")

# Передаємо ці змінні в AuthManager
auth_manager = AuthManager(SHEET_ID, CREDENTIALS_FILE)

# Ініціалізація бота
bot = telebot.TeleBot(TOKEN)

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
        phone_number = auth_manager.clean_phone_number(phone_number)  # Очищуємо номер

        print(f"[DEBUG] Отримано номер: {phone_number}")

        try:
            user_data = auth_manager.check_user_in_database(phone_number)
            print(f"[DEBUG] Відповідь від auth.py: {user_data}")

            if user_data:
                # Кешуємо дані для подальшої роботи
                cached_data = {
                    "id": user_data["id"],
                    "name": user_data["name"],
                    "email": user_data["email"],
                    "role": user_data["role"]
                }
                print(f"[DEBUG] Користувач збережений у кеш: {cached_data}")

                # Відправляємо лише ім'я користувача у відповідь
                bot.send_message(
                    message.chat.id,
                    f"✅ Вітаю, *{user_data['name']}*! Ви успішно ідентифіковані. 🎉",
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
            print(f"❌ ПОМИЛКА: {e}")

if __name__ == "__main__":
    print("✅ Бот запущено. Очікування повідомлень...")
    
    bot.remove_webhook()  # Очищаємо Webhook перед запуском polling
    bot.polling(none_stop=True)
