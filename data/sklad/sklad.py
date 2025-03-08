import os
import json
import gspread
import asyncio
from fpdf import FPDF
from datetime import datetime
import pytz
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery, WebAppInfo
from menu.keyboards import get_restart_keyboard
from urllib.parse import urlencode

# Налаштування часової зони для Києва
kyiv_tz = pytz.timezone("Europe/Kiev")

# Завантаження облікових даних із JSON-рядка
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
if not CREDENTIALS_FILE:
    raise ValueError("❌ Змінна CREDENTIALS_FILE не знайдена!")
try:
    CREDENTIALS_JSON = json.loads(CREDENTIALS_FILE)
except json.JSONDecodeError as e:
    raise ValueError(f"❌ Помилка розбору JSON в CREDENTIALS_FILE: {e}")

FONT_PATH = os.path.join("/app/config/fonts", "DejaVuSans.ttf")

async def get_sklad_menu(user_data: dict):
    """
    Формує меню для розділу складу.
    URL WebApp отримує query-параметри з ім'ям та телефоном користувача.
    """
    user_name = user_data.get("name", "незнайомий")
    user_phone = user_data.get("phone", "не вказано")
    params = urlencode({"name": user_name, "phone": user_phone})
    url = f"https://velykyykit.github.io/Agenhd/webapp/order/order.html?{params}"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛒 Зробити Замовлення",
            web_app=WebAppInfo(url=url)
        )],
        [InlineKeyboardButton(text="📊 Перевірити Наявність", callback_data="check_stock")]
    ])

async def handle_sklad(message: types.Message, user_data: dict):
    """Обробка розділу складу."""
    menu = await get_sklad_menu(user_data)
    await message.answer("📦 Ви у розділі складу. Оберіть дію:", reply_markup=menu)

async def get_all_stock():
    """Отримання даних складу."""
    gc = gspread.service_account_from_dict(CREDENTIALS_JSON)
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

async def show_all_stock(call: CallbackQuery):
    """Генерація PDF зі списком товарів та надсилання користувачу."""
    await call.answer()
    wait_message = await call.message.answer("⏳ Зачекайте, документ формується...")
    try:
        if not os.path.exists(FONT_PATH):
            await call.message.answer("❌ Помилка: Файл шрифту DejaVuSans.ttf не знайдено!")
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
        await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=wait_message.message_id)
        file = FSInputFile(filename)
        await call.message.answer_document(file, caption="📄 Ось список наявних товарів на складі.")
        os.remove(filename)
    except Exception as e:
        await call.message.answer("❌ Помилка при створенні документа!")
        print(f"❌ ПОМИЛКА: {e}")
