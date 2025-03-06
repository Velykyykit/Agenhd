import os
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, Group
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Конфігурація
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

class OrderDialog(StatesGroup):
    select_course = State()
    select_items = State()
    confirm_order = State()

# Функція отримання курсів у дві колонки
async def get_courses_in_columns(**kwargs):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("dictionary")
    courses = worksheet.get_all_records()
    formatted_courses = [{"name": c["course"], "short": c["short"]} for c in courses]
    return {
        "left_courses": formatted_courses[:10],
        "right_courses": formatted_courses[10:]
    }

# Функція отримання товарів для вибраного курсу
async def get_items(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course")
    if not selected_course:
        return {"items": []}

    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("SKLAD")
    data = worksheet.get_all_records()

    filtered_items = [
        {"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": 0}
        for item in data if item["course"].strip() == selected_course.strip()
    ]

    return {"items": filtered_items}

# Функція зміни кількості товарів
async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str, change: int):
    cart = manager.dialog_data.setdefault("cart", {})
    cart[item_id] = max(0, cart.get(item_id, 0) + change)
    await manager.refresh()

# Діалог вибору курсу та товарів
order_dialog = Dialog(
    Window(
        Const("📚 Оберіть курс:"),
        Group(
            Select(
                Format("🎓 {item[name]}"), items="left_courses", id="left_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=lambda c, w, m, item_id: m.start(OrderDialog.select_items, {"selected_course": item_id})
            ),
            Select(
                Format("🎓 {item[name]}"), items="right_courses", id="right_course_select",
                item_id_getter=lambda item: item["short"],
                on_click=lambda c, w, m, item_id: m.start(OrderDialog.select_items, {"selected_course": item_id})
            ),
            width=2
        ),
        state=OrderDialog.select_course,
        getter=get_courses_in_columns,
    ),
    Window(
        Const("🛍️ Оберіть товари:"),
        Group(
            Select(
                Format("🏷️ {item[name]} - 💰 {item[price]} грн | 🛒 {cart.get(item[id], 0)}"),
                items="items", id="item_select",
                item_id_getter=lambda item: item["id"],
            ),
            Select(
                Format("➖"), id=lambda item: f"minus_{item['id']}",
                items="items",
                item_id_getter=lambda item: item["id"],
                on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, -1),
            ),
            Select(
                Format("➕"), id=lambda item: f"plus_{item['id']}",
                items="items",
                item_id_getter=lambda item: item["id"],
                on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, 1),
            ),
            width=2
        ),
        Button(Const("✅ Оформити замовлення"), id="confirm_order", on_click=lambda c, w, m: m.switch_to(OrderDialog.confirm_order)),
        state=OrderDialog.select_items,
        getter=get_items,
    )
)
