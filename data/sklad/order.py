import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Select, Group, Row
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

# Функція отримання списку курсів із таблиці "dictionary"
# У колонці "course" - повна назва, у "short" - коротка назва.
# Обмежуємо до 20 курсів і розбиваємо їх на два стовпці по 10.
async def get_courses(**kwargs):
    courses = worksheet_courses.get_all_records()
    courses = [{"name": c["course"], "short": c["short"]} for c in courses][:20]
    left_courses = courses[:10]
    right_courses = courses[10:]
    return {"left_courses": left_courses, "right_courses": right_courses}

# Обробник натискання на курс.
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    # item_id містить коротку назву курсу
    manager.dialog_data["selected_course"] = item_id
    await callback.answer(f"Обрано курс: {item_id}")
    # Тут можна додати перехід до наступного вікна для вибору товарів

# Вікно вибору курсу
course_window = Window(
    Const("📚 Оберіть курс:"),
    # Row розташовує два Group поруч (горизонтально)
    Row(
        Group(
            Select(
                Format("🎓 {item[name]}"),
                items="left_courses",  # Дані для першої колонки
                id="left_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            )
        ),
        Group(
            Select(
                Format("🎓 {item[name]}"),
                items="right_courses",  # Дані для другої колонки
                id="right_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            )
        )
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

# Створення діалогу з одним вікном
order_dialog = Dialog(course_window)
