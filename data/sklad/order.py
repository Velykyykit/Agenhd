import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Column
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
async def get_items(dialog_manager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course")
    if not selected_course:
        return {"items": []}

    all_items = worksheet_items.get_all_records()
    items = [item for item in all_items if item["course"] == selected_course]

    return {"items": items}


# Обробник натискання на курс
async def select_course(callback: types.CallbackQuery, button: Button, manager):
    manager.dialog_data["selected_course"] = button.widget_id
    await manager.switch_to(OrderSG.select_item)


# Обробник зміни кількості товарів
async def change_quantity(callback: types.CallbackQuery, button: Button, manager, item_id: str, delta: int):
    cart = manager.dialog_data.setdefault("cart", {})
    cart[item_id] = max(cart.get(item_id, 0) + delta, 0)
    await manager.update()


# Вікно вибору курсу
course_window = Window(
    Const("📚 Оберіть курс:"),
    Row(
        Column(
            *[
                Button(Format("🎓 {item[name]}"), id=item["short"], on_click=select_course)
                for item in (await get_courses())["col1"]
            ]
        ),
        Column(
            *[
                Button(Format("🎓 {item[name]}"), id=item["short"], on_click=select_course)
                for item in (await get_courses())["col2"]
            ]
        ),
    ),
    state=OrderSG.select_course,
)

# Вікно вибору товарів
item_window = Window(
    Const("🛍 Виберіть товари:"),
    *[
        Row(
            Format("{item[name]} - {item[price]} грн 🛒 {cart.get(item[id], 0)} шт"),
            Button(Const("➖"), id=f"minus_{item['id']}", on_click=lambda c, w, m, item_id=item["id"]: change_quantity(c, w, m, item_id, -1)),
            Button(Const("➕"), id=f"plus_{item['id']}", on_click=lambda c, w, m, item_id=item["id"]: change_quantity(c, w, m, item_id, 1)),
        )
        for item in (await get_items())["items"]
    ],
    state=OrderSG.select_item,
)

# Створення діалогу
order_dialog = Dialog(course_window, item_window)
