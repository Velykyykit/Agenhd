from fpdf import FPDF
import os
import gspread
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu.keyboards import get_restart_keyboard

# Налаштовуємо часовий пояс для Києва
kyiv_tz = pytz.timezone("Europe/Kiev")

# Використовуємо шлях до credentials.json із змінних Railway
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
print("🔍 Шлях до credentials.json:", CREDENTIALS_PATH)
print("📂 Файл існує:", os.path.exists(CREDENTIALS_PATH))

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
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("SKLAD")

    data = worksheet.get_all_values()
    stock_items = []

    for row in data[1:]:  # Пропускаємо заголовок
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
    """Генерує PDF-файл зі списком товарів і надсилає користувачу."""
    wait_message = bot.send_message(message.chat.id, "⏳ Зачекайте, документ формується...")

    try:
        items = get_all_stock()
        now = datetime.now(kyiv_tz).strftime("%Y-%m-%d_%H-%M")

        filename = f"sklad_HD_{now}.pdf"

        pdf = FPDF()
        pdf.set_font("Helvetica", "", 12)  # Використання стандартного шрифту
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("DejaVu", "", 12)

        pdf.cell(200, 10, f"Наявність товарів на складі (станом на {now})", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("DejaVu", "", 10)
        pdf.cell(20, 8, "ID", border=1, align="C")
        pdf.cell(50, 8, "Курс", border=1, align="C")
        pdf.cell(50, 8, "Товар", border=1, align="C")
        pdf.cell(20, 8, "На складі", border=1, align="C")
        pdf.cell(20, 8, "Доступно", border=1, align="C")
        pdf.cell(20, 8, "Ціна", border=1, align="C")
        pdf.ln()

        for item in items:
            pdf.cell(20, 8, str(item["id"]), border=1, align="C")
            pdf.cell(50, 8, item["course"], border=1, align="L")
            pdf.cell(50, 8, item["name"], border=1, align="L")
            pdf.cell(20, 8, str(item["stock"]), border=1, align="C")
            pdf.cell(20, 8, str(item["available"]), border=1, align="C")
            pdf.cell(20, 8, f"{item['price']}₴", border=1, align="C")
            pdf.ln()

        pdf.output(filename, "F")

        bot.delete_message(chat_id=message.chat.id, message_id=wait_message.message_id)

        with open(filename, "rb") as file:
            bot.send_document(message.chat.id, file, caption="📄 Ось список наявних товарів на складі.")

        os.remove(filename)

    except Exception as e:
        bot.edit_message_text("❌ Помилка при створенні документа!", chat_id=message.chat.id, message_id=wait_message.message_id)
        print(f"❌ ПОМИЛКА: {e}")

def show_courses_for_order(bot, message):
    """Показує список курсів для замовлення."""
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("dictionary")  # Аркуш із курсами

    courses = worksheet.col_values(1)  # Отримати всі назви курсів
    if not courses:
        bot.send_message(message.chat.id, "❌ Немає доступних курсів для замовлення.")
        return

    markup = InlineKeyboardMarkup()
    for course in courses:
        markup.add(InlineKeyboardButton(course, callback_data=f"course_{course}"))

    bot.send_message(message.chat.id, "📚 Оберіть курс для замовлення:", reply_markup=markup)
