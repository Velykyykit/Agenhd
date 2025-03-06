import os
import datetime
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, Row, Column, Group
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Конфігурація
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

class OrderDialog(StatesGroup):
    select_course = State()
    select_items = State()
    confirm_order = State()

async def get_courses(**kwargs):
    """Отримання курсів із таблиці `dictionary`."""
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("dictionary")
    courses = worksheet.get_all_records(numericise_ignore=['all'], head=1)
    
    formatted_courses = [
        {"name": course.get("course"), "short": course.get("short")} for course in courses
    ]
    return formatted_courses

async def get_courses_in_columns(**kwargs):
    """Розбиття курсів на два стовпці по 10."""
    courses = await get_courses()
    left_column = courses[:10]
    right_column = courses[10:]
    return {"left_courses": left_column, "right_courses": right_column}

async def get_items(dialog_manager: DialogManager, **kwargs):
    """Отримання товарів для вибраного курсу."""
    selected_course = dialog_manager.dialog_data.get("selected_course")
    
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("SKLAD")
    data = worksheet.get_all_records(numericise_ignore=['all'], head=1)
    
    items = [
        {"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 0}
        for item in data if item["course"] == selected_course
    ]
    return {"items": items}

async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str, change: int):
    """Зміна кількості товарів."""
    cart = manager.dialog_data.setdefault("cart", {})
    cart[item_id] = max(0, cart.get(item_id, 0) + change)
    await manager.refresh()

order_dialog = Dialog(
    Window(
        Const("📚 Оберіть курс:"),
        Group(
            Select(
                Format("🎓 {item[name]}"), items="left_courses", id="left_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
            ),
            Select(
                Format("🎓 {item[name]}"), items="right_courses", id="right_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
            ),
            width=2
        ),
        state=OrderDialog.select_course,
        getter=get_courses_in_columns,
    ),
    Window(
        Const("🛍️ Оберіть товари:"),
        Column(
            Row(
                Button(Const("➖"), id=lambda item: f"minus_{item['id']}", on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, -1)),
                Format("🏷️ {item[name]} - 💰 {item[price]} грн | 🛒 {item[quantity]}"),
                Button(Const("➕"), id=lambda item: f"plus_{item['id']}", on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, 1))
            ),
            items="items"
        ),
        Button(Const("✅ Оформити замовлення"), id="confirm_order", on_click=lambda c, w, m: m.switch_to(OrderDialog.confirm_order)),
        state=OrderDialog.select_items,
        getter=get_items,
    )
)
