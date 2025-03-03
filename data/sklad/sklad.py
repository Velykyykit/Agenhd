import os
import gspread
import asyncio
from fpdf import FPDF
from datetime import datetime
import pytz
from aiogram import Bot, types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from menu.keyboards import get_restart_keyboard

router = Router()

# Налаштовуємо часовий пояс для Києва
kyiv_tz = pytz.timezone("Europe/Kiev")

CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
FONT_PATH = os.path.join("/app/config/fonts", "DejaVuSans.ttf")


def get_sklad_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Зробити Замовлення", callback_data="order")],
        [InlineKeyboardButton(text="📊 Перевірити Наявність", callback_data="check_stock")]
    ])


@router.callback_query(lambda call: call.data == "sklad")
async def handle_sklad(call: types.CallbackQuery):
    """Обробка складу."""
    await call.message.answer("📦 Ви у розділі складу. Оберіть дію:", reply_markup=get_sklad_menu())
    keyboard = await get_restart_keyboard()
    await call.message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=keyboard)


async def get_all_stock():
    """Отримує всі товари зі складу."""
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


@router.callback_query(lambda call: call.data == "check_stock")
async def show_all_stock(call: types.CallbackQuery):
    """Генерує PDF-файл зі списком товарів і надсилає користувачу."""
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

        await call.message.delete()
        file = FSInputFile(filename)
        await call.message.answer_document(file, caption="📄 Ось список наявних товарів на складі.")

        os.remove(filename)

    except Exception as e:
        await call.message.answer("❌ Помилка при створенні документа!")
        print(f"❌ ПОМИЛКА: {e}")


@router.callback_query(lambda call: call.data == "order")
async def show_courses_for_order(call: types.CallbackQuery):
    """Показує список курсів для замовлення."""
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(os.getenv("SHEET_SKLAD"))
    worksheet = sh.worksheet("dictionary")  # Аркуш із курсами

    courses = await asyncio.to_thread(worksheet.col_values, 1)
    if not courses:
        await call.message.answer("❌ Немає доступних курсів для замовлення.")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=course, callback_data=f"course_{course}")] for course in courses
    ])

    await call.message.answer("📚 Оберіть курс для замовлення:", reply_markup=markup)
