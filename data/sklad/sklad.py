from fpdf import FPDF
import os
import gspread
import pytz
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu.keyboards import get_restart_keyboard

def get_sklad_menu():
    """Меню складу."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Зробити Замовлення", callback_data="order"))
    markup.add(InlineKeyboardButton("📊 Перевірити Наявність", callback_data="check_stock"))
    return markup

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

def generate_pdf(filename, items, title):
    """Генерує PDF-файл зі списком товарів."""
    # Отримуємо поточний час у Києві
    kyiv_tz = pytz.timezone("Europe/Kiev")
    now = datetime.now(kyiv_tz).strftime("%d.%m.%Y %H:%M")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Використовуємо стандартний шрифт без емодзі
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, f"{title}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Дата та час (Україна): {now}", ln=True, align="C")
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

    pdf.output(filename)

def show_all_stock(bot, message):
    """Створює 2 PDF-файли та надсилає користувачу."""
    items = get_all_stock()

    # Файл 1: Усі товари на складі
    filename_all = f"stock_all_{message.chat.id}.pdf"
    generate_pdf(filename_all, items, "Повний список товарів на складі")

    # Файл 2: Товари, які можна замовити (доступно > 0)
    available_items = [item for item in items if item["available"] > 0]
    filename_available = f"stock_available_{message.chat.id}.pdf"
    generate_pdf(filename_available, available_items, "Список доступних товарів")

    # Відправляємо файли
    with open(filename_all, "rb") as file:
        bot.send_document(message.chat.id, file, caption="📄 Повний список товарів на складі.")

    with open(filename_available, "rb") as file:
        bot.send_document(message.chat.id, file, caption="📄 Список доступних товарів.")

    # Видаляємо тимчасові файли
    os.remove(filename_all)
    os.remove(filename_available)
