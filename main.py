import os
import telebot
from menu.keyboards import get_phone_keyboard
from config.auth import AuthManager

# Отримуємо змінні з Railway
TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

if not TOKEN or not SHEET_ID or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено необхідні змінні середовища!")

auth_manager = AuthManager(SHEET_ID, CREDENTIALS_FILE)
bot = telebot.TeleBot(TOKEN)

# **Створюємо глобальний словник для збереження даних**
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Запит на номер телефону при першому запуску."""
    markup = get_phone_keyboard()
    bot.send_message(
        message.chat.id,
        "Поділіться номером для аутентифікації:",
        reply_markup=markup
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Перевірка номера телефону та збереження даних у пам'яті бота."""
    if message.contact:
        phone_number = auth_manager.clean_phone_number(message.contact.phone_number)

        print(f"[DEBUG] Отримано номер: {phone_number}")

        try:
            user_name = auth_manager.check_user_in_database(phone_number)

            if user_name:
                # **Зберігаємо дані в словник**
                user_data[message.chat.id] = {
                    "name": user_name,
                    "phone": phone_number
                }

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
            print(f"❌ ПОМИЛКА: {e}")

@bot.message_handler(commands=['whoami'])
def who_am_i(message):
    """Повертає ім'я та номер телефону користувача, якщо він вже авторизований."""
    user_info = user_data.get(message.chat.id)
    
    if user_info:
        bot.send_message(
            message.chat.id,
            f"👤 Ви авторизовані як: *{user_info['name']}*\n📞 Ваш номер: {user_info['phone']}",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Ви ще не авторизувалися. Надішліть /start для початку."
        )

if __name__ == "__main__":
    print("✅ Бот запущено. Очікування повідомлень...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
