import asyncio
import logging
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# Аутентифікація
from config.auth import AuthManager
# Логіка складу
from data.sklad.sklad import handle_sklad, show_all_stock
# Клавіатури
from menu.keyboards import get_phone_keyboard, get_restart_keyboard
# aiogram-dialog
from aiogram_dialog import setup_dialogs, StartMode, DialogManager
from data.sklad.order import order_dialog, OrderSG  
# Перегляд замовлень
from data.For_me.me import show_my_orders

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
PORT = int(os.getenv("PORT", 5000))

if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища!")

CREDENTIALS_JSON = json.loads(CREDENTIALS_FILE)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)
auth_manager = AuthManager(SHEET_ID, CREDENTIALS_JSON)

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Склад", callback_data="sklad")],
        [InlineKeyboardButton(text="📝 Завдання", callback_data="tasks")],
        [InlineKeyboardButton(text="🙋‍♂️ Для мене", callback_data="forme")]
    ])

@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.answer("📲 Поділіться номером для аутентифікації:", reply_markup=await get_phone_keyboard())

@router.message(F.contact)
async def handle_contact(message: types.Message):
    if message.contact.user_id != message.from_user.id:
        await message.answer("❌ Скористайтеся кнопкою '📲 Поділитися номером'.")
        return
    phone_number = auth_manager.clean_phone_number(message.contact.phone_number)
    try:
        user_data = await auth_manager.check_user_in_database(phone_number)
        if user_data:
            await message.answer(f"✅ Вітаю, *{user_data['name']}*! Ви успішно ідентифіковані. 🎉", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
            await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())
        else:
            await message.answer("❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")
    except Exception as e:
        logging.error(f"❌ ПОМИЛКА: {e}")

@router.callback_query(F.data == "sklad")
async def handle_sklad_call(call: types.CallbackQuery):
    await call.answer()
    await handle_sklad(call.message)

@router.callback_query(F.data == "check_stock")
async def handle_stock_check(call: types.CallbackQuery):
    await call.answer()
    await show_all_stock(call)

@router.callback_query(F.data == "tasks")
async def handle_tasks(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("📝 Розділ 'Завдання' ще в розробці.")

@router.callback_query(F.data == "forme")
async def handle_forme(call: types.CallbackQuery):
    await call.answer()
    await show_my_orders(call.message)

@router.message(F.text == "🔄 Почати спочатку")
async def restart_handler(message: types.Message):
    await message.answer("🔄 Починаємо спочатку", reply_markup=ReplyKeyboardRemove())
    await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())

setup_dialogs(dp)
dp.include_router(order_dialog)

@router.callback_query(F.data == "order")
async def start_order_dialog(call: types.CallbackQuery, dialog_manager: DialogManager):
    await call.answer()
    await dialog_manager.start(OrderSG.select_course, mode=StartMode.RESET_STACK)

async def get_courses(request):
    try:
        gc = gspread.service_account_from_dict(CREDENTIALS_JSON)
        sh = gc.open_by_key(SHEET_SKLAD)
        worksheet_courses = sh.worksheet("dictionary")
        rows = worksheet_courses.get_all_records()
        courses = [{"name": row["course"], "short": row["short"]} for row in rows]
        return web.json_response({"courses": courses})
    except Exception as e:
        logging.error(f"❌ Помилка отримання курсів: {e}")
        return web.json_response({"error": "Помилка сервера"}, status=500)

app = web.Application()
app.router.add_get("/api/get_courses", get_courses)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.info("🚀 Запуск сервера...")
    asyncio.run(main())
