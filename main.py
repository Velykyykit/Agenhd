import os
import telebot
from menu.keyboards import get_phone_keyboard, get_restart_keyboard
from config.auth import AuthManager
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from data.sklad.sklad import handle_sklad, show_all_stock, show_courses_for_order

# Отримуємо змінні з Railway
TOKEN = os.getenv("TOKEN")  
SHEET_ID = os.getenv("SHEET_ID")  
SHEET_SKLAD = os.getenv("SHEET_SKLAD")  
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")  

# Перевіряємо, чи всі змінні встановлені
if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища! Перевірте Railway.")

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
        "📲 Поділіться номером для аутентифікації:",  
        reply_markup=markup  
    )

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    """Обробка номера телефону та аутентифікація."""
    if message.contact:
        phone_number = message.contact.phone_number
        phone_number = auth_manager.clean_phone_number(phone_number)

        print(f"[DEBUG] Отримано номер: {phone_number}")

        try:
            user_data = auth_manager.check_user_in_database(phone_number)
            print(f"[DEBUG] Відповідь від auth.py: {user_data}")

            if user_data:
                remove_keyboard = ReplyKeyboardRemove()

                bot.send_message(
                    message.chat.id,
                    f"✅ Вітаю, *{user_data['name']}*! Ви успішно ідентифіковані. 🎉",
                    parse_mode="Markdown",
                    reply_markup=remove_keyboard
                )

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
        handle_sklad(bot, call.message)
    
    elif call.data == "tasks":
        bot.send_message(call.message.chat.id, "📝 Розділ 'Завдання' ще в розробці.")
    
    elif call.data == "forme":
        bot.send_message(call.message.chat.id, "🙋‍♂️ Розділ 'Для мене' ще в розробці.")

@bot.callback_query_handler(func=lambda call: call.data == "check_stock")
def handle_stock_check(call):
    """Обробляє запит на перевірку наявності товарів."""
    show_all_stock(bot, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "order")
def handle_order(call):
    """Обробляє запит на оформлення замовлення."""
    show_courses_for_order(bot, call.message)

@bot.message_handler(func=lambda message: message.text == "🔄 Почати спочатку")
def restart_bot(message):
    """Обробка натискання кнопки '🔄 Почати спочатку'."""
    send_main_menu(message)

if __name__ == "__main__":
    print("✅ Бот запущено. Очікування повідомлень...")
    
    bot.remove_webhook()
    bot.polling(none_stop=True)
