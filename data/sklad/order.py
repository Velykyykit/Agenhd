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
worksheet_items = sh.worksheet("SKLAD")

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

# Отримання списку товарів для вибраного курсу
async def get_items(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course")
    if not selected_course:
        return {"items": []}
    all_items = worksheet_items.get_all_records()
    items = [item for item in all_items if item["course"] == selected_course]
    return {"items": items}

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["selected_course"] = button.widget_id
    await callback.answer("🚧 Функція ще в розробці!")
    await manager.switch_to(OrderSG.select_item)

# Вікно вибору курсу
course_window = Window(
    Const("📚 Оберіть курс (тимчасова заглушка):"),
    Row(
        Column(
            Select(
                Format("🎓 {item[name]}"),
                items="col1",
                id="left_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            )
        ),
        Column(
            Select(
                Format("🎓 {item[name]}"),
                items="col2",
                id="right_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            )
        )
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

# Створення діалогу
order_dialog = Dialog(course_window)
