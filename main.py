import asyncio
import logging
import os
import json
import gspread
from aiohttp import web  # ✅ Додаємо aiohttp для API сервера

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (
    ReplyKeyboardRemove, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage

# Аутентифікація
from config.auth import AuthManager

# Логіка складу
from data.sklad.sklad import handle_sklad, show_all_stock  

# Клавіатури
from menu.keyboards import get_phone_keyboard, get_restart_keyboard

# === aiogram-dialog ===
from aiogram_dialog import setup_dialogs, StartMode
from aiogram_dialog import DialogManager

# Перегляд замовлень («Для мене»)
from data.For_me.me import show_my_orders

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища!")

# Завантаження облікових даних Google Sheets
try:
    CREDENTIALS_JSON = json.loads(CREDENTIALS_FILE)
except json.JSONDecodeError as e:
    raise ValueError(f"❌ Помилка розбору JSON в CREDENTIALS_FILE: {e}")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Глобальний словник для збереження даних користувачів після аутентифікації
USER_DATA = {}

# Підключення до Google Sheets
gc = gspread.service_account_from_dict(CREDENTIALS_JSON)
sh = gc.open_by_key(SHEET_ID)
contact_sheet = sh.worksheet("contact")  # Лист "contact" з даними користувачів

auth_manager = AuthManager(SHEET_ID, CREDENTIALS_JSON)

def get_main_menu():
    """Головне меню із кнопками."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Склад", callback_data="sklad")],
        [InlineKeyboardButton(text="📝 Завдання", callback_data="tasks")],
        [InlineKeyboardButton(text="🙋‍♂️ Для мене", callback_data="forme")]
    ])

async def update_telegram_id(user_id, telegram_id):
    """Оновлює Telegram ID користувача у базі, якщо він ще не записаний."""
    try:
        all_data = contact_sheet.get_all_values()
        for idx, row in enumerate(all_data[1:], start=2):  # Пропускаємо заголовки
            if row[0] == user_id:  # ID користувача знаходиться в першому стовпці
                if len(row) < 5 or not row[4]:  # Якщо поле Telegram ID (стовпець 5) порожнє
                    contact_sheet.update_cell(idx, 5, telegram_id)
                    logging.info(f"✅ Оновлено Telegram ID {telegram_id} для користувача {user_id}")
                break
    except Exception as e:
        logging.error(f"❌ Помилка оновлення Telegram ID: {e}")

@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    """Надсилає запит на поділитися номером телефону."""
    await message.answer(
        "📲 Поділіться номером для аутентифікації:",
        reply_markup=await get_phone_keyboard()
    )

@router.message(F.contact)
async def handle_contact(message: types.Message):
    """Обробка отриманого контакту та аутентифікація."""
    if message.contact.user_id != message.from_user.id:
        await message.answer("❌ Скористайтеся кнопкою '📲 Поділитися номером'.")
        return

    phone_number = auth_manager.clean_phone_number(message.contact.phone_number)
    logging.info(f"[DEBUG] Отримано номер: {phone_number}")

    try:
        user_data = await auth_manager.check_user_in_database(phone_number)
        logging.info(f"[DEBUG] Відповідь від auth.py: {user_data}")
        if user_data:
            # Отримуємо ID користувача з першого стовпця таблиці `contact`
            user_id = user_data.get("id", "невідомо")
            user_name = user_data.get("name", "незнайомий")
            
            # Оновлюємо Telegram ID у Google Sheets
            await update_telegram_id(user_id, message.from_user.id)

            # Зберігаємо дані користувача в глобальному словнику
            USER_DATA[message.from_user.id] = {
                "id": user_id,  # ID з першого стовпця Google Sheets
                "name": user_name,
                "phone": phone_number,
                "tg_id": message.from_user.id
            }

            await message.answer(
                f"✅ Вітаю, *{user_name}*! Ви успішно ідентифіковані. 🎉",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())
        else:
            await message.answer("❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")
    except Exception as e:
        await message.answer("❌ Сталася помилка під час перевірки номера. Спробуйте пізніше.")
        logging.error(f"❌ ПОМИЛКА: {e}")

### ✅ **ОБРОБНИКИ CALLBACK-КНОПОК**
@router.callback_query(F.data == "sklad")
async def handle_sklad_call(call: types.CallbackQuery):
    """Обробник натискання кнопки '📦 Склад'."""
    await call.answer()
    user_data = USER_DATA.get(call.from_user.id, {
        "id": "невідомо",
        "name": call.from_user.first_name, 
        "phone": "не вказано",
        "tg_id": call.from_user.id
    })
    await handle_sklad(call.message, user_data)

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

setup_dialogs(dp)

async def main():
    """Запуск бота в режимі polling та сервера WebApp API."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
