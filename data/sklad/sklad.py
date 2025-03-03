import os
import gspread
import asyncio
from fpdf import FPDF
from datetime import datetime
import pytz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from menu.keyboards import get_restart_keyboard

# Налаштовуємо часовий пояс для Києва
kyiv_tz = pytz.timezone("Europe/Kiev")

CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
FONT_PATH = os.path.join("/app/config/fonts", "DejaVuSans.ttf")

async def get_sklad_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Зробити Замовлення", callback_data="order")],
        [InlineKeyboardButton(text="📊 Перевірити Наявність", callback_data="check_stock")]
    ])

async def handle_sklad(message):
    await message.answer("📦 Ви у розділі складу. Оберіть дію:", reply_markup=await get_sklad_menu())
    keyboard = await get_restart_keyboard()
    await message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=keyboard)

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

async def show_all_stock(message):
    wait_message = await message.answer("⏳ Зачекайте, документ формується...")

    try:
        if not os.path.exists(FONT_PATH):
            await message.answer("❌ Помилка: Файл шрифту DejaVuSans.ttf не знайдено!")
            return

        items = await get_all_stock()
        now = datetime.now(kyiv_tz).strftime("%Y-%m-%d_%H-%M")
        filename = f"sklad_HD_{now}.pdf"

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
        pdf.set_font("DejaVu", '', 12)

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

        await message.bot.delete_message(chat_id=message.chat.id, message_id=wait_message.message_id)

        file = FSInputFile(filename)
        await message.answer_document(file, caption="📄 Ось список наявних товарів на складі.")

        os.remove(filename)

    except Exception as e:
        await message.answer("❌ Помилка при створенні документа!")
        print(f"❌ ПОМИЛКА: {e}")
