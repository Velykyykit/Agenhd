import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Column, Select, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Конфігурація Google Sheets
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

# Підключення до Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")
worksheet_sklad = sh.worksheet("SKLAD")

# Класи станів для діалогу
class OrderSG(StatesGroup):
    select_course = State()
    select_items = State()

# Отримання списку курсів (дві колонки по 10)
async def get_courses(**kwargs):
    courses = worksheet_courses.get_all_records()
    courses = [{"name": c["course"], "short": c["short"]} for c in courses][:20]
    col1 = courses[:10]  # Перший стовпець (10 курсів)
    col2 = courses[10:]  # Другий стовпець (10 курсів)
    return {"col1": col1, "col2": col2}

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, button: Button, manager: DialogManager):
    selected_course = button.widget_id.split("_")[-1]
    await callback.answer(f"✅ Ви вибрали курс: {selected_course}")
    manager.dialog_data["selected_course"] = selected_course
    await manager.next()

# Отримання списку товарів для курсу
async def get_items(**kwargs):
    selected_course = kwargs["dialog_manager"].dialog_data.get("selected_course", "")
    if not selected_course:
        return {"items": []}
    sklad_data = worksheet_sklad.get_all_records()
    items = [
        {"id": str(i["id"]), "name": i["name"], "price": i["price"]}
        for i in sklad_data if i["course"] == selected_course
    ]
    return {"items": items}

# Заглушка для кнопки "🛒 Додати в кошик"
async def add_to_cart(callback: types.CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("✅ Товари додані в кошик!")

# Вікно вибору курсу
course_window = Window(
    Const("📚 Оберіть курс:"),
    Row(
        Column(
            Select(
                Format("🎓 {item[name]}"), items="col1", id="left_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            ),
        ),
        Column(
            Select(
                Format("🎓 {item[name]}"), items="col2", id="right_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=select_course
            ),
        ),
    ),
    state=OrderSG.select_course,
    getter=get_courses,
)

# Вікно вибору товарів
items_window = Window(
    Const("📦 Товари курсу:"),
    Column(
        Select(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн"),
            items="items", id="item_select", item_id_getter=lambda item: item["id"]
        ),
    ),
    Row(
        Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, b, m: m.back()),
        Button(Const("🛒 Додати в кошик"), id="add_to_cart", on_click=add_to_cart),
    ),
    state=OrderSG.select_items,
    getter=get_items,
)

# Створення діалогу
order_dialog = Dialog(course_window, items_window)
