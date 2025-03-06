import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Select, Group
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")

class OrderSG(StatesGroup):
    select_course = State()

async def get_courses(**kwargs):
    """
    Зчитуємо до 20 курсів.
    У колонках 'course' і 'short' мають бути відповідні дані.
    """
    all_rows = worksheet_courses.get_all_records()
    # Обмежуємо до 20
    courses = [{"name": row["course"], "short": row["short"]} for row in all_rows][:20]
    return {"courses": courses}

async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    """
    Обробник натискання на кнопку курсу.
    item_id = коротка назва курсу (row["short"]).
    """
    await callback.answer(f"Обрано курс: {item_id}")

course_window = Window(
    Const("📚 Оберіть курс:"),
    Group(
        Select(
            Format("🎓 {item[name]}"),
            items="courses",               # список курсів із getter
            id="course_select",
            item_id_getter=lambda item: item["short"],
            on_click=select_course
        ),
        width=2,   # 2 кнопки в одному рядку
        height=10  # максимум 10 рядків (разом 20 кнопок)
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

order_dialog = Dialog(course_window)
