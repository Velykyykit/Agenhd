from fpdf import FPDF
import os
import gspread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu.keyboards import get_restart_keyboard

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
    CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
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
    items = get_all_stock()

    # Назва файлу (уникнення конфліктів)
    filename = f"stock_{message.chat.id}.pdf"

    # Створюємо PDF-документ
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style="", size=12)

    # Заголовок
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, "📦 Наявність товарів на складі", ln=True, align="C")
    pdf.ln(10)

    # Створюємо таблицю
    pdf.set_font("Arial", size=10)
    pdf.cell(20, 8, "ID", border=1, align="C")
    pdf.cell(50, 8, "Курс", border=1, align="C")
    pdf.cell(50, 8, "Товар", border=1, align="C")
    pdf.cell(20, 8, "На складі", border=1, align="C")
    pdf.cell(20, 8, "Доступно", border=1, align="C")
    pdf.cell(20, 8, "Ціна", border=1, align="C")
    pdf.ln()

    # Додаємо дані в таблицю
    for item in items:
        pdf.cell(20, 8, str(item["id"]), border=1, align="C")
        pdf.cell(50, 8, item["course"], border=1, align="L")
        pdf.cell(50, 8, item["name"], border=1, align="L")
        pdf.cell(20, 8, str(item["stock"]), border=1, align="C")
        pdf.cell(20, 8, str(item["available"]), border=1, align="C")
        pdf.cell(20, 8, f"{item['price']}₴", border=1, align="C")
        pdf.ln()

    # Зберігаємо PDF
    pdf.output(filename)

    # Відправляємо файл користувачу
    with open(filename, "rb") as file:
        bot.send_document(message.chat.id, file, caption="📄 Ось список наявних товарів на складі.")

    # Видаляємо тимчасовий файл
    os.remove(filename)

def show_courses_for_order(bot, message):
    """Показує список курсів для замовлення."""
    CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("dictionary")  # Вказати назву аркуша з курсами

    courses = worksheet.col_values(1)  # Отримати всі назви курсів
    markup = InlineKeyboardMarkup()

    for course in courses:
        markup.add(InlineKeyboardButton(course, callback_data=f"course_{course}"))

    bot.send_message(message.chat.id, "📚 Оберіть курс для замовлення:", reply_markup=markup)
