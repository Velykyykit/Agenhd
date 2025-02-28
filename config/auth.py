from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from keyboards import main_menu_keyboard, request_phone_keyboard
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config.credentials import SHEET_ID

# Підключення до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

def check_user_in_database(phone_number):
    users = sheet.get_all_records()
    for user in users:
        if str(user["Телефон відповідального"]) == phone_number:
            return user["Ім'я Прізвище відповідального"], user["Навчальний центр"]
    return None, None

async def process_phone_number(message: types.Message, state: FSMContext):
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        await message.answer("Будь ласка, скористайтесь кнопкою для відправки номера.", reply_markup=request_phone_keyboard())
        return
    
    user_name, center = check_user_in_database(phone_number)
    
    if user_name:
        await message.answer(f"Вітаю, {user_name}! Ви авторизовані як представник {center}.", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Ваш номер не знайдено у системі. Будь ласка, зверніться до адміністратора.", reply_markup=ReplyKeyboardRemove())
    
    await state.finish()

def register_auth_handlers(dp: Dispatcher):
    dp.register_message_handler(process_phone_number, content_types=types.ContentType.CONTACT)

