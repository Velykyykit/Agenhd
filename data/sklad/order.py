import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Row, Column, Select, Group
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Конфігурація Google Sheets
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

# Підключення до Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")

# Класи станів для діалогу
class OrderSG(StatesGroup):
    select_course = State()
    select_item = State()

# Отримання списку курсів (дві колонки по 10)
async def get_courses(**kwargs):
    courses = worksheet_courses.get_all_records()
    courses = [{"name": c["course"], "short": c["short"]} for c in courses][:20]  # Обмеження до 20 курсів

    col1 = courses[:10]  # Перший стовпець (10 курсів)
    col2 = courses[10:]  # Другий стовпець (10 курсів)

    return {"col1": col1, "col2": col2}

# Обробник вибору курсу\nasync def select_course(callback: types.CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("🚧 Ця функція ще в розробці!")

# Вікно вибору курсу\ncourse_window = Window(
    Const("📚 Оберіть курс (тимчасова заглушка):"),
    Group(
        Select(
            Format("🎓 {item[name]}"), items="col1", id="left_course_select",
            item_id_getter=lambda item: item["short"],
            on_click=select_course
        ),
        Select(
            Format("🎓 {item[name]}"), items="col2", id="right_course_select",
            item_id_getter=lambda item: item["short"],
            on_click=select_course
        ),
        width=2
    ),
    state=OrderSG.select_course,
    getter=get_courses,
)

# Створення діалогу\norder_dialog = Dialog(course_window)
