import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

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

# Отримуємо курси (до 20)
async def get_courses(**kwargs):
    rows = worksheet_courses.get_all_records()
    # Беремо не більше 20
    courses = [
        {"name": row["course"], "short": row["short"]}
        for row in rows
    ][:20]
    return {"courses": courses}

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    # item_id = коротка назва курсу
    manager.dialog_data["selected_course"] = item_id
    await callback.answer(f"Ви обрали курс: {item_id}")

# Вікно вибору курсу
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
        width=2,    # 2 кнопки в одному рядку
        height=10,  # разом 10 рядків, тобто 2х10=20 кнопок
        id="courses_scroller"
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

# Створюємо діалог
order_dialog = Dialog(course_window)
