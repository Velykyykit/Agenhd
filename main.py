import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from config.settings import TOKEN
from config.auth import AuthManager
from data.sklad.sklad import handle_sklad, show_all_stock, show_courses_for_order

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Менеджер аутентифікації
auth_manager = AuthManager()

# Функції клавіатур
def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📲 Поділитися номером", request_contact=True))
    return keyboard

def get_restart_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Почати спочатку"))
    return keyboard

def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📦 Склад", callback_data="sklad"))
    markup.add(InlineKeyboardButton("📝 Завдання", callback_data="tasks"))
    markup.add(InlineKeyboardButton("🙋‍♂️ Для мене", callback_data="forme"))
    return markup

# Обробник команди /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("📲 Поділіться номером для аутентифікації:", reply_markup=get_phone_keyboard())

# Обробка контактних даних
@dp.message_handler(content_types=types.ContentType.CONTACT)
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
                reply_markup=ReplyKeyboardRemove()  # Прибираємо клавіатуру після авторизації
            )
            await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())
        else:
            await message.answer("❌ Ваш номер не знайдено у базі. Зверніться до адміністратора.")

    except Exception as e:
        await message.answer("❌ Сталася помилка під час перевірки номера. Спробуйте пізніше.")
        logging.error(f"❌ ПОМИЛКА: {e}")

# Обробник вибору меню
@dp.callback_query_handler(lambda call: call.data in ["sklad", "tasks", "forme"])
async def handle_main_menu(call: types.CallbackQuery):
    if call.data == "sklad":
        await handle_sklad(bot, call.message)
    elif call.data == "tasks":
        await call.message.answer("📝 Розділ 'Завдання' ще в розробці.")
    elif call.data == "forme":
        await call.message.answer("🙋‍♂️ Розділ 'Для мене' ще в розробці.")

# Обробник перевірки складу
@dp.callback_query_handler(lambda call: call.data == "check_stock")
async def handle_stock_check(call: types.CallbackQuery):
    await show_all_stock(bot, call.message)

# Обробник оформлення замовлення
@dp.callback_query_handler(lambda call: call.data == "order")
async def handle_order(call: types.CallbackQuery):
    await show_courses_for_order(bot, call.message)

# Обробник кнопки "🔄 Почати спочатку"
@dp.message_handler(lambda message: message.text == "🔄 Почати спочатку")
async def restart_bot(message: types.Message):
    await message.answer("📌 Оберіть розділ:", reply_markup=get_main_menu())

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
