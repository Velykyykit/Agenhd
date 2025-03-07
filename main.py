import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# Аутентифікація (ваш модуль)
from config.auth import AuthManager

# Логіка складу
from data.sklad.sklad import handle_sklad, show_all_stock

# Клавіатури
from menu.keyboards import get_phone_keyboard, get_restart_keyboard

# === aiogram-dialog ===
from aiogram_dialog import setup_dialogs, StartMode, DialogManager
from data.sklad.order import order_dialog, OrderSG  # Ваш діалог

# Перегляд замовлень («Для мене»)
from data.For_me.me import show_my_orders

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища!")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

auth_manager = AuthManager(SHEET_ID, CREDENTIALS_FILE)

def get_main_menu():
    """Головне меню із кнопками."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Склад", callback_data="sklad")],
        [InlineKeyboardButton(text="📝 Завдання", callback_data="tasks")],
        [InlineKeyboardButton(text="🙋‍♂️ Для мене", callback_data="forme")]
    ])

@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    """Надсилає запит на поділитися номером телефону."""
    await message.answer(
        "📲 Поділіться номером для аутентифікації:",
        reply_markup=await get_phone_keyboard()
    )

@router.message(F.contact)
async def handle_contact(message: types.Message):
    """
    Обробляє отриманий контакт і виконує аутентифікацію.
    Перевіряє, чи контакт належить відправнику.
    """
    if message.contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Скористайтеся кнопкою '📲 Поділитися номером' для відправки саме вашого номера телефону."
        )
        return

    phone_number = auth_manager.clean_phone_number(message.contact.phone_number)
    logging.info(f"[DEBUG] Отримано номер: {phone_number}")

    try:
        user_data = await auth_manager.check_user_in_database(phone_number)
        logging.info(f"[DEBUG] Відповідь від auth.py: {user_data}")
        if user_data:
            await message.answer(
                f"✅ Вітаю, *{user_data['name']}*! Ви успішно ідентифіковані. 🎉",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())
            await message.answer(
                "🔄 Якщо хочете повернутися назад, натисніть кнопку:",
                reply_markup=await get_restart_keyboard()
            )
        else:
            await message.answer("❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")
    except Exception as e:
        await message.answer("❌ Сталася помилка під час перевірки номера. Спробуйте пізніше.")
        logging.error(f"❌ ПОМИЛКА: {e}")

@router.callback_query(F.data == "sklad")
async def handle_sklad_call(call: types.CallbackQuery):
    """Переходить у розділ 'Склад'."""
    await call.answer()
    await handle_sklad(call.message)

@router.callback_query(F.data == "check_stock")
async def handle_stock_check(call: types.CallbackQuery):
    """Перевіряє наявність товарів (генерує PDF)."""
    await call.answer()
    await show_all_stock(call)

@router.callback_query(F.data == "tasks")
async def handle_tasks(call: types.CallbackQuery):
    """Розділ 'Завдання' (поки в розробці)."""
    await call.answer()
    await call.message.answer("📝 Розділ 'Завдання' ще в розробці.")

@router.callback_query(F.data == "forme")
async def handle_forme(call: types.CallbackQuery):
    """Розділ 'Для мене' – перегляд замовлень."""
    await call.answer()
    await show_my_orders(call.message)

@router.message(F.text == "🔄 Почати спочатку")
async def restart_handler(message: types.Message):
    """Кнопка 'Почати спочатку' повертає користувача в головне меню."""
    await message.answer("🔄 Починаємо спочатку", reply_markup=ReplyKeyboardRemove())
    await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())
    await message.answer(
        "🔄 Якщо хочете повернутися назад, натисніть кнопку:",
        reply_markup=await get_restart_keyboard()
    )

# Підключаємо middleware для aiogram-dialog
setup_dialogs(dp)
dp.include_router(order_dialog)

@router.callback_query(F.data == "order")
async def start_order_dialog(call: types.CallbackQuery, dialog_manager: DialogManager):
    """Запуск діалогу для оформлення замовлення."""
    await call.answer()
    await dialog_manager.start(OrderSG.select_course, mode=StartMode.RESET_STACK)

# === Інтеграція веб-сервера FastAPI ===
from fastapi import FastAPI
import uvicorn

# Імпортуємо веб-маршрути з модуля data/sklad/order.py
from data.sklad.order import order_router

# Створюємо FastAPI додаток
app = FastAPI()

# Головна сторінка веб-сервера
@app.get("/")
def root():
    return {"message": "Hello from Web App & Telegram Bot!"}

# Включаємо маршрути веб-інтерфейсу (вони будуть доступні за префіксом /order)
app.include_router(order_router, prefix="/order")

# При старті FastAPI запускаємо бота у фоні
@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
