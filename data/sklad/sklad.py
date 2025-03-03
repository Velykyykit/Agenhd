import os
import gspread
import asyncio
from fpdf import FPDF
from datetime import datetime
import pytz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu.keyboards import get_restart_keyboard

# Налаштовуємо часовий пояс для Києва
kyiv_tz = pytz.timezone("Europe/Kiev")

CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
FONT_PATH = os.path.join("/app/config/fonts", "DejaVuSans.ttf")
print(f"✅ CREDENTIALS_FILE знайдено: {CREDENTIALS_FILE}")
async def get_sklad_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Зробити Замовлення", callback_data="order"))
    markup.add(InlineKeyboardButton("📊 Перевірити Наявність", callback_data="check_stock"))
    return markup

async def handle_sklad(bot, message):
    await message.answer("📦 Ви у розділі складу. Оберіть дію:", reply_markup=await get_sklad_menu())
    await message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=get_restart_keyboard())

async def get_all_stock():
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("SKLAD")

    data = await asyncio.to_thread(worksheet.get_all_values)
    stock_items = [{
        "id": row[0],
        "course": row[1],
        "name": row[2],
        "stock": int(row[3]) if row[3].isdigit() else 0,
        "available": int(row[4]) if row[4].isdigit() else 0,
        "price": int(row[5]) if row[5].isdigit() else 0
    } for row in data[1:]]

    return stock_items

async def show_all_stock(bot, message):
    wait_message = await message.answer("⏳ Зачекайте, документ формується...")

    try:
        items = await get_all_stock()
        now = datetime.now(kyiv_tz).strftime("%Y-%m-%d_%H-%M")
        filename = f"sklad_HD_{now}.pdf"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, f"Наявність товарів на складі (станом на {now})", ln=True, align="C")
        pdf.ln(10)

        pdf.cell(30, 8, "ID", border=1, align="C")
        pdf.cell(80, 8, "Товар", border=1, align="C")
        pdf.cell(30, 8, "На складі", border=1, align="C")
        pdf.cell(30, 8, "Ціна", border=1, align="C")
        pdf.ln()

        for item in items:
            pdf.cell(30, 8, str(item["id"]), border=1, align="C")
            pdf.cell(80, 8, item["name"], border=1, align="L")
            pdf.cell(30, 8, str(item["stock"]), border=1, align="C")
            pdf.cell(30, 8, f"{item['price']}₴", border=1, align="C")
            pdf.ln()

        pdf.output(filename)

        await bot.delete_message(chat_id=message.chat.id, message_id=wait_message.message_id)

        with open(filename, "rb") as file:
            await bot.send_document(message.chat.id, file, caption="📄 Ось список наявних товарів на складі.")

        os.remove(filename)

    except Exception as e:
        await message.answer("❌ Помилка при створенні документа!")
        print(f"❌ ПОМИЛКА: {e}")

async def show_courses_for_order(bot, message):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("dictionary")

    courses = await asyncio.to_thread(worksheet.col_values, 1)
    if not courses:
        await message.answer("❌ Немає доступних курсів для замовлення.")
        return

    markup = InlineKeyboardMarkup()
    for course in courses:
        markup.add(InlineKeyboardButton(course, callback_data=f"course_{course}"))

    await message.answer("📚 Оберіть курс для замовлення:", reply_markup=markup)
