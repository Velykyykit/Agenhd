import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, 
                           InlineKeyboardButton, ReplyKeyboardRemove)
from config.auth import AuthManager
from data.sklad.sklad import router as sklad_router
import os

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Отримуємо змінні середовища
TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища! Перевірте Railway.")

# Ініціалізація бота, диспетчера та роутера
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(sklad_router)  # Підключаємо маршрутизатор складу

# Менеджер аутентифікації
auth_manager = AuthManager(SHEET_ID, CREDENTIALS_FILE)


def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Склад", callback_data="sklad")],
        [InlineKeyboardButton(text="📝 Завдання", callback_data="tasks")],
        [InlineKeyboardButton(text="🙋‍♂️ Для мене", callback_data="forme")]
    ])


def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Поділитися номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# Обробник команди /start
@dp.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.answer("📲 Поділіться номером для аутентифікації:", reply_markup=get_phone_keyboard())


# Обробник вибору меню
@dp.callback_query(F.data == "sklad")
async def handle_main_menu(call: types.CallbackQuery):
    await call.answer()
    await sklad_router.resolve_event(call)


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
