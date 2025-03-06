import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Row, Column
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
    """Зчитуємо курси (до 20) і ділимо на дві колонки."""
    courses = worksheet_courses.get_all_records()
    courses = [{"name": c["course"], "short": c["short"]} for c in courses][:20]

    col1 = courses[:10]  # Перші 10 курсів – ліва колонка
    col2 = courses[10:]  # Наступні 10 курсів – права колонка
    return {"col1": col1, "col2": col2}

async def select_course(callback: types.CallbackQuery, button: Button, manager: DialogManager):
    """Обробник натискання на курс."""
    await callback.answer(f"Обрано курс: {button.widget_id} (заглушка)")

course_window = Window(
    Const("📚 Оберіть курс:"),
    Row(
        Column(
            *[
                Button(
                    Format("🎓 {item[name]}"),
                    id=f"course_{item['short']}",
                    on_click=select_course
                ) for item in ("col1")  # Цей список сформуємо у getter
            ]
        ),
        Column(
            *[
                Button(
                    Format("🎓 {item[name]}"),
                    id=f"course_{item['short']}",
                    on_click=select_course
                ) for item in ("col2")
            ]
        ),
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

order_dialog = Dialog(course_window)
