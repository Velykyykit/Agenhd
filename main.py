import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove)
from config.auth import AuthManager
from data.sklad.sklad import handle_sklad, show_all_stock, show_courses_for_order
from menu.keyboards import get_phone_keyboard, get_restart_keyboard

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Отримуємо змінні середовища
TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")

# Логування змінних середовища
logger.info(f"🔍 Перевірка змінних середовища:")
logger.info(f"✅ TOKEN: {'Знайдено' if TOKEN else '❌ НЕ ЗНАЙДЕНО'}")
logger.info(f"✅ SHEET_ID: {SHEET_ID if SHEET_ID else '❌ НЕ ЗНАЙДЕНО'}")
logger.info(f"✅ SHEET_SKLAD: {SHEET_SKLAD if SHEET_SKLAD else '❌ НЕ ЗНАЙДЕНО'}")
logger.info(f"✅ CREDENTIALS_FILE: {CREDENTIALS_FILE if CREDENTIALS_FILE else '❌ НЕ ЗНАЙДЕНО'}")

# Перевірка наявності критичних змінних
missing_vars = []
if not TOKEN:
    missing_vars.append("TOKEN")
if not SHEET_ID:
    missing_vars.append("SHEET_ID")
if not SHEET_SKLAD:
    missing_vars.append("SHEET_SKLAD")
if not CREDENTIALS_FILE:
    missing_vars.append("CREDENTIALS_FILE")

if missing_vars:
    logger.error(f"❌ Відсутні критичні змінні середовища: {', '.join(missing_vars)}")
    raise ValueError("⛔ Зупинка програми через відсутність критичних змінних середовища!")

logger.info("✅ Всі необхідні змінні середовища знайдено. Продовжуємо роботу!")

if not TOKEN or not SHEET_ID or not SHEET_SKLAD or not CREDENTIALS_FILE:
    raise ValueError("❌ Не знайдено змінні середовища! Перевірте Railway.")

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()  # Використовуємо Router

# Менеджер аутентифікації
auth_manager = AuthManager(SHEET_ID, CREDENTIALS_FILE)

def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 Склад", callback_data="sklad"))
    markup.add(InlineKeyboardButton("📝 Завдання", callback_data="tasks"))
    markup.add(InlineKeyboardButton("🙋‍♂️ Для мене", callback_data="forme"))
    return markup

# Обробник команди /start
@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.answer("📲 Поділіться номером для аутентифікації:", reply_markup=await get_phone_keyboard())

# Обробка контактних даних
@router.message(F.contact)
async def handle_contact(message: types.Message):
    phone_number = message.contact.phone_number
    phone_number = auth_manager.clean_phone_number(phone_number)

    logging.info(f"[DEBUG] Отримано номер: {phone_number}")

    try:
        user_data = await asyncio.to_thread(auth_manager.check_user_in_database, phone_number)
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
@router.callback_query(F.data.in_(["sklad", "tasks", "forme"]))
async def handle_main_menu(call: types.CallbackQuery):
    if call.data == "sklad":
        await handle_sklad(bot, call.message)
    elif call.data == "tasks":
        await call.message.answer("📝 Розділ 'Завдання' ще в розробці.")
    elif call.data == "forme":
        await call.message.answer("🙋‍♂️ Розділ 'Для мене' ще в розробці.")

# Обробник перевірки складу
@router.callback_query(F.data == "check_stock")
async def handle_stock_check(call: types.CallbackQuery):
    await show_all_stock(bot, call.message)

# Обробник оформлення замовлення
@router.callback_query(F.data == "order")
async def handle_order(call: types.CallbackQuery):
    await show_courses_for_order(bot, call.message)

# Обробник кнопки "🔄 Почати спочатку"
@router.message(F.text == "🔄 Почати спочатку")
async def restart_bot(message: types.Message):
    await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())

# Запуск бота
async def main():
    logging.info("✅ Видаляємо старий вебхук...")
    await bot.delete_webhook(drop_pending_updates=True)  # Видаляємо вебхук
    
    dp.include_router(router)  # Додаємо маршрутизатор у диспетчер
    logging.info("🚀 Бот запускається...")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
