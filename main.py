import asyncio
import logging
import os
import json

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (
    ReplyKeyboardRemove, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage

# Аутентифікація (оновлений модуль)
from config.auth import AuthManager

# Логіка складу
from data.sklad.sklad import handle_sklad, show_all_stock

# Клавіатури
from menu.keyboards import get_phone_keyboard, get_restart_keyboard

# === aiogram-dialog ===
from aiogram_dialog import setup_dialogs, StartMode
from aiogram_dialog import DialogManager
from data.sklad.order import order_dialog, OrderSG  

# Перегляд замовлень («Для мене»)
from data.For_me.me import show_my_orders

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища!")

# Перетворення JSON-рядка у Python-словник
try:
    CREDENTIALS_JSON = json.loads(CREDENTIALS_FILE)
except json.JSONDecodeError as e:
    raise ValueError(f"❌ Помилка розбору JSON в CREDENTIALS_FILE: {e}")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Передаємо JSON безпосередньо
auth_manager = AuthManager(SHEET_ID, CREDENTIALS_JSON)

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
    """
    if message.contact.user_id != message.from_user.id:
        await message.answer("❌ Скористайтеся кнопкою '📲 Поділитися номером'")
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
        else:
            await message.answer("❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")
    except Exception as e:
        await message.answer("❌ Сталася помилка під час перевірки номера. Спробуйте пізніше.")
        logging.error(f"❌ ПОМИЛКА: {e}")

# Замість DialogRegistry: підключаємо middleware для aiogram-dialog
setup_dialogs(dp)
dp.include_router(order_dialog)

async def main():
    """Запуск бота в режимі polling."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
