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
    # Подальші стани можна додати, якщо потрібно

# Функція отримання списку курсів з аркуша "dictionary"
# У колонці "course" - повна назва, у "short" - коротка назва
async def get_courses(**kwargs):
    courses = worksheet_courses.get_all_records()
    # Обмеження до перших 20 курсів
    courses = [{"name": c["course"], "short": c["short"]} for c in courses][:20]
    col1 = courses[:10]  # перший стовпець - 10 курсів
    col2 = courses[10:]  # другий стовпець - 10 курсів
    return {"left_courses": col1, "right_courses": col2}

# Обробник вибору курсу (натискання на кнопку курсу)
async def select_course(callback: types.CallbackQuery, button: Button, manager: DialogManager):
    # Зберігаємо коротку назву вибраного курсу
    manager.dialog_data["selected_course"] = button.widget_id
    await callback.answer(f"Обрано курс: {button.widget_id}")
    # Тут можна перейти до наступного стану, якщо потрібно
    # await manager.switch_to(OrderSG.select_item)

# Вікно вибору курсу
course_window = Window(
    Const("📚 Оберіть курс:"),
    # Розбиваємо кнопки курсів на два стовпці за допомогою Row з двома Column
    Row(
        Column(
            Select(
                Format("🎓 {item[name]}"),
                items="left_courses",
                id="left_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            )
        ),
        Column(
            Select(
                Format("🎓 {item[name]}"),
                items="right_courses",
                id="right_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            )
        )
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

# Створення діалогу, який поки містить тільки вікно вибору курсу
order_dialog = Dialog(course_window)
