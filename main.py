import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from config.auth import AuthManager
from data.sklad.sklad import handle_sklad, show_all_stock, show_courses_for_order
from menu.keyboards import get_phone_keyboard, get_restart_keyboard

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Отримання змінних середовища
TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища!")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Менеджер аутентифікації
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
    await message.answer("📲 Поділіться номером для аутентифікації:", reply_markup=await get_phone_keyboard())

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
            await message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=await get_restart_keyboard())
        else:
            await message.answer("❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")
    except Exception as e:
        await message.answer("❌ Сталася помилка під час перевірки номера. Спробуйте пізніше.")
        logging.error(f"❌ ПОМИЛКА: {e}")

@router.callback_query(F.data == "sklad")
async def handle_sklad_call(call: types.CallbackQuery):
    await call.answer()
    await handle_sklad(call.message)

@router.callback_query(F.data == "check_stock")
async def handle_stock_check(call: types.CallbackQuery):
    await call.answer()
    await show_all_stock(call)

@router.callback_query(F.data == "order")
async def handle_order(call: types.CallbackQuery):
    await call.answer()
    await show_courses_for_order(bot, call.message)

@router.callback_query(F.data == "tasks")
async def handle_tasks(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("📝 Розділ 'Завдання' ще в розробці.")

@router.callback_query(F.data == "forme")
async def handle_forme(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("🙋‍♂️ Розділ 'Для мене' ще в розробці.")

@router.message(F.text == "🔄 Почати спочатку")
async def restart_handler(message: types.Message):
    await message.answer("🔄 Починаємо спочатку", reply_markup=ReplyKeyboardRemove())
    await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())
    await message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=await get_restart_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
