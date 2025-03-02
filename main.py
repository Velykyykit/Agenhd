import os
import telebot
from menu.keyboards import get_phone_keyboard, get_restart_keyboard  # Додаємо get_restart_keyboard
from config.auth import AuthManager  # Імпортуємо клас аутентифікації
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from data.sklad.sklad import handle_sklad  # Імпортуємо обробник складу


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
    markup = get_phone_keyboard()  # Тільки кнопка "Поділитися номером"
    
    bot.send_message(
        message.chat.id,
        "📲 Поділіться номером для аутентифікації:",  
        reply_markup=markup  
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Обробка номера телефону та аутентифікація."""
    if message.contact:
        phone_number = message.contact.phone_number
        phone_number = auth_manager.clean_phone_number(phone_number)  # Очищуємо номер

        print(f"[DEBUG] Отримано номер: {phone_number}")

        try:
            user_data = auth_manager.check_user_in_database(phone_number)
            print(f"[DEBUG] Відповідь від auth.py: {user_data}")

            if user_data:
                # Видаляємо кнопку "Поділитися номером"
                remove_keyboard = ReplyKeyboardRemove()

                # Відправляємо вітальне повідомлення
                bot.send_message(
                    message.chat.id,
                    f"✅ Вітаю, *{user_data['name']}*! Ви успішно ідентифіковані. 🎉",
                    parse_mode="Markdown",
                    reply_markup=remove_keyboard  # Видаляємо кнопку після авторизації
                )

                # Показуємо головне меню та кнопку "Почати спочатку"
                send_main_menu(message)

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

def send_main_menu(message):
    """Показує головне меню з кнопкою 'Почати спочатку'."""
    bot.send_message(
        message.chat.id,
        "📌 Оберіть розділ:",
        reply_markup=get_main_menu()
    )
    
    # Додаємо кнопку "🔄 Почати спочатку"
    bot.send_message(
        message.chat.id,
        "🔄 Якщо хочете повернутися, натисніть кнопку:",
        reply_markup=get_restart_keyboard()
    )

def get_main_menu():
    """Головне меню з кнопками: Склад, Завдання, Для мене."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 Склад", callback_data="sklad"))
    markup.add(InlineKeyboardButton("📝 Завдання", callback_data="tasks"))
    markup.add(InlineKeyboardButton("🙋‍♂️ Для мене", callback_data="forme"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data in ["sklad", "tasks", "forme"])
def handle_main_menu(call):
    """Обробляє вибір кнопок у головному меню."""
    if call.data == "sklad":
        handle_sklad(bot, call.message)  # Викликаємо функцію складу
    
    elif call.data == "tasks":
        bot.send_message(call.message.chat.id, "📝 Розділ 'Завдання' ще в розробці.")
    
    elif call.data == "forme":
        bot.send_message(call.message.chat.id, "🙋‍♂️ Розділ 'Для мене' ще в розробці.")

@bot.message_handler(func=lambda message: message.text == "🔄 Почати спочатку")
def restart_bot(message):
    """Обробка натискання кнопки '🔄 Почати спочатку'."""
    bot.send_message(
        message.chat.id,
        "🔄 Починаємо спочатку. Оберіть розділ:",
        reply_markup=get_main_menu()
    )
    
    # Повторно показуємо кнопку "🔄 Почати спочатку"
    bot.send_message(
        message.chat.id,
        "🔄 Якщо хочете повернутися, натисніть кнопку:",
        reply_markup=get_restart_keyboard()
    )

if __name__ == "__main__":
    print("✅ Бот запущено. Очікування повідомлень...")
    
    bot.remove_webhook()  # Очищаємо Webhook перед запуском polling
    bot.polling(none_stop=True)
