from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu.keyboards import get_restart_keyboard
import gspread
import os

def get_sklad_menu():
    """Меню складу."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Зробити Замовлення", callback_data="order"))
    markup.add(InlineKeyboardButton("📊 Перевірити Наявність", callback_data="check_stock"))
    return markup

def handle_sklad(bot, message):
    """Функція для обробки складу."""
    bot.send_message(message.chat.id, "📦 Ви у розділі складу. Оберіть дію:", reply_markup=get_sklad_menu())
    bot.send_message(message.chat.id, "🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=get_restart_keyboard())

def get_all_stock():
    """Отримує всі товари зі складу."""
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("SKLAD")

    data = worksheet.get_all_values()
    stock_items = []

    for row in data[1:]:
        stock_items.append({
            "id": row[0],
            "course": row[1],
            "name": row[2],
            "stock": int(row[3]) if row[3].isdigit() else 0,
            "available": int(row[4]) if row[4].isdigit() else 0,
            "price": int(row[5]) if row[5].isdigit() else 0
        })

    return stock_items

def show_all_stock(bot, message):
    """Відображає всі товари на складі."""
    items = get_all_stock()
    response = "📦 Усі товари на складі:\n\n"

    for item in items:
        response += f"🔹 [{item['id']}] {item['name']} ({item['course']})\n"
        response += f"   🔢 {item['stock']} шт. | 🛒 Доступно: {item['available']} шт. | 💰 {item['price']}₴\n\n"

    bot.send_message(message.chat.id, response)

def show_courses_for_order(bot, message):
    """Показує список курсів для замовлення."""
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("dictionary")

    courses = worksheet.col_values(1)
    markup = InlineKeyboardMarkup()

    for course in courses:
        markup.add(InlineKeyboardButton(course, callback_data=f"course_{course}"))

    bot.send_message(message.chat.id, "📚 Оберіть курс для замовлення:", reply_markup=markup)
