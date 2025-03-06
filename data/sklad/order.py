import os
import gspread
import time
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Button, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Підключення до Google Sheets
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
SHEET_SKLAD = os.getenv("SHEET_SKLAD")

gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")
worksheet_sklad = sh.worksheet("SKLAD")

# Кеш для збереження даних
CACHE_EXPIRY = 300  # 5 хвилин
cache = {
    "courses": {"data": [], "timestamp": 0},
    "products": {"data": {}, "timestamp": 0}
}

# Стан вибору курсу, товару і кількості
class OrderSG(StatesGroup):
    select_course = State()
    show_products = State()
    select_quantity = State()

async def get_courses(**kwargs):
    now = time.time()
    if now - cache["courses"]["timestamp"] < CACHE_EXPIRY:
        return {"courses": cache["courses"]["data"]}
    
    rows = worksheet_courses.get_all_records()
    courses = [{"name": row["course"], "short": row["short"]} for row in rows][:20]
    
    cache["courses"] = {"data": courses, "timestamp": now}
    return {"courses": courses}

async def get_products(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course", None)
    if not selected_course:
        return {"products": []}

    now = time.time()
    if selected_course in cache["products"] and now - cache["products"][selected_course]["timestamp"] < CACHE_EXPIRY:
        return {"products": cache["products"][selected_course]["data"]}

    rows = worksheet_sklad.get_all_records()
    products = [
        {"id": str(index), "name": row["name"], "price": row["price"]}
        for index, row in enumerate(rows, start=1) if row["course"] == selected_course
    ]

    cache["products"][selected_course] = {"data": products, "timestamp": now}
    dialog_manager.dialog_data["products"] = products  # Зберігаємо список товарів

    return {"products": products}

async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обробка вибору курсу"""
    manager.dialog_data["selected_course"] = item_id
    await callback.answer(f"✅ Ви обрали курс: {item_id}")
    await manager.next()

async def select_product(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    """При натисканні на товар відкриваємо екран вибору кількості"""
    manager.dialog_data["selected_product"] = item_id
    manager.dialog_data["quantity"] = 1  # Початкова кількість товару
    await manager.next()

async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, action: str):
    """Змінюємо кількість товару"""
    quantity = manager.dialog_data.get("quantity", 1)
    if action == "increase":
        quantity += 1
    elif action == "decrease" and quantity > 1:
        quantity -= 1
    manager.dialog_data["quantity"] = quantity
    await callback.answer()
    await manager.dialog().update()

async def confirm_selection(callback: types.CallbackQuery, widget, manager: DialogManager):
    """Підтвердження вибору товару"""
    selected_product = manager.dialog_data.get("selected_product", "❌ Невідомий товар")
    quantity = manager.dialog_data.get("quantity", 1)
    await callback.answer(f"✅ Додано {quantity} шт. товару {selected_product} у кошик!")
    await manager.done()

course_window = Window(
    Const("📚 Оберіть курс:"),
    ScrollingGroup(
        Select(
            Format("🎓 {item[name]}"),
            items="courses",
            id="course_select",
            item_id_getter=lambda item: item["short"],
            on_click=select_course
        ),
        width=2,
        height=10,
        id="courses_scroller",
        hide_on_single_page=True
    ),
    state=OrderSG.select_course,
    getter=get_courses
)

product_window = Window(
    Format("📦 Товари курсу {dialog_data[selected_course]}:"),
    ScrollingGroup(
        Select(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн"),
            items="products",
            id="product_select",
            item_id_getter=lambda item: item["id"],
            on_click=select_product  # Переходимо до екрану вибору кількості
        ),
        width=1,
        height=10,
        id="products_scroller",
        hide_on_single_page=True
    ),
    Row(
        Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
    ),
    state=OrderSG.show_products,
    getter=get_products
)

quantity_window = Window(
    Format("🖼 Фото товару тут\n📦 Товар: {dialog_data[selected_product]}"),
    Row(
        Button(Const("➖"), id="decrease_quantity", on_click=lambda c, w, m: change_quantity(c, w, m, "decrease")),
        Button(Format("{dialog_data[quantity]}"), id="quantity_display"),  # Виправлено
        Button(Const("➕"), id="increase_quantity", on_click=lambda c, w, m: change_quantity(c, w, m, "increase")),
    ),
    Row(
        Button(Const("✅ Підтвердити"), id="confirm_selection", on_click=confirm_selection),
        Button(Const("🔙 Назад"), id="back_to_products", on_click=lambda c, w, m: m.back()),
    ),
    state=OrderSG.select_quantity
)

order_dialog = Dialog(course_window, product_window, quantity_window)
