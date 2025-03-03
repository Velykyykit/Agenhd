import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardRemove
)
from config.auth import AuthManager
from data.sklad.sklad import handle_sklad, show_all_stock
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

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

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
@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.answer("📲 Поділіться номером для аутентифікації:", reply_markup=get_phone_keyboard())

# Обробка контактних даних
@router.message(F.contact)
async def handle_contact(message: types.Message):
    phone_number = message.contact.phone_number
    phone_number = auth_manager.clean_phone_number(phone_number)

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

# Обробник вибору меню
@router.callback_query(F.data == "sklad")
async def handle_sklad_call(call: types.CallbackQuery):
    await handle_sklad(call.message)

# Обробник перевірки складу
@router.callback_query(F.data == "check_stock")
async def handle_stock_check(call: types.CallbackQuery):
    await show_all_stock(call)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
