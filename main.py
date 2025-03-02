import os
import telebot
from telebot.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
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

def get_main_menu():
    """Головне меню у вигляді вбудованих кнопок."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 Склад", callback_data="warehouse"))
    markup.add(InlineKeyboardButton("📌 Створити Завдання", callback_data="create_task"))
    markup.add(InlineKeyboardButton("📝 Мої Завдання", callback_data="my_tasks"))
    return markup

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

                # **Прибираємо кнопку "📲 Поділитися номером"**
                bot.send_message(
                    message.chat.id,
                    f"✅ Вітаю, *{user_name}*! Ви успішно ідентифіковані. 🎉",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardRemove()  # Видаляє стару клавіатуру
                )

                # **Надсилаємо головне меню**
                bot.send_message(
                    message.chat.id,
                    "Оберіть дію:",
                    reply_markup=get_main_menu()
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

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обробка вибору користувача в головному меню."""
    if call.data == "warehouse":
        bot.send_message(call.message.chat.id, "📦 Ви обрали *Склад*", parse_mode="Markdown")
    elif call.data == "create_task":
        bot.send_message(call.message.chat.id, "📌 Ви обрали *Створити Завдання*", parse_mode="Markdown")
    elif call.data == "my_tasks":
        bot.send_message(call.message.chat.id, "📝 Ви обрали *Мої Завдання*", parse_mode="Markdown")

if __name__ == "__main__":
    print("✅ Бот запущено. Очікування повідомлень...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
