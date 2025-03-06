import os
import gspread
import logging
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Налаштування логування (Railway)
logging.basicConfig(level=logging.INFO)

# Конфігурація Google Sheets
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

# Підключення до Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")

# Стан вибору курсу
class OrderSG(StatesGroup):
    select_course = State()

# Отримання курсів (до 20)
async def get_courses(**kwargs):
    rows = worksheet_courses.get_all_records()
    courses = [{"name": row["course"], "short": row["short"]} for row in rows][:20]
    return {"courses": courses}

# Обробник вибору курсу з логуванням
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    selected_course = item_id
    manager.dialog_data["selected_course"] = selected_course

    # 🔥 Запис у логи Railway
    logging.info(f"[COURSE SELECTED] Користувач {callback.from_user.id} обрав курс: {selected_course}")

    await callback.answer(f"✅ Ви обрали курс: {selected_course}")

# Вікно вибору курсу (без кнопок прокрутки)
course_window = Window(
    Const("📚 Оберіть курс:"),
    ScrollingGroup(
        Select(
            Format("🎓 {item[name]}"),
            items="courses",
            id="course_select",
            item_id_getter=lambda item: item["short"],
            on_click=select_course
        ),
        width=2,  # 2 стовпці
        height=10,  # 10 рядків (разом 20 кнопок)
        id="courses_scroller",
        hide_on_single_page=True  # 🔥 Прибирає кнопки прокрутки, якщо всі елементи вміщуються
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

# Створюємо діалог
order_dialog = Dialog(course_window)
