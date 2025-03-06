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
    "products": {"data": {}, "timestamp": 0}  # Кеш для кожного курсу
}

# Стан вибору курсу і товару
class OrderSG(StatesGroup):
    select_course = State()
    show_products = State()

async def get_courses(**kwargs):
    """Отримує список курсів з кешу або Google Sheets."""
    now = time.time()
    if now - cache["courses"]["timestamp"] < CACHE_EXPIRY:
        return {"courses": cache["courses"]["data"]}
    
    rows = worksheet_courses.get_all_records()
    courses = [{"name": row["course"], "short": row["short"]} for row in rows][:20]
    
    cache["courses"] = {"data": courses, "timestamp": now}
    return {"courses": courses}

async def get_products(dialog_manager: DialogManager, **kwargs):
    """Отримує список товарів для вибраного курсу з кешу або Google Sheets."""
    selected_course = dialog_manager.dialog_data.get("selected_course", None)
    if not selected_course:
        return {"products": []}
    
    now = time.time()
    if selected_course in cache["products"] and now - cache["products"][selected_course]["timestamp"] < CACHE_EXPIRY:
        return {"products": cache["products"][selected_course]["data"]}
    
    rows = worksheet_sklad.get_all_records()
    products = [
        {"id": row["id"], "name": row["name"], "price": row["price"]}
        for row in rows if row["course"] == selected_course
    ]
    
    cache["products"][selected_course] = {"data": products, "timestamp": now}
    return {"products": products}

async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_course"] = item_id
    await callback.answer(f"✅ Ви обрали курс: {item_id}")
    await manager.next()

async def add_to_cart(callback: types.CallbackQuery, widget, manager: DialogManager):
    selected_course = manager.dialog_data.get("selected_course", "❌ Невідомий курс")
    await callback.answer(f"✅ Додано товари курсу {selected_course} у кошик!")

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
            item_id_getter=lambda item: str(item["id"]),
            on_click=lambda c, w, m, item_id: c.answer(f"ℹ️ Ви вибрали товар {item_id}")
        ),
        width=1,
        height=10,
        id="products_scroller",
        hide_on_single_page=True
    ),
    Row(
        Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
        Button(Const("🛒 Додати в кошик"), id="add_to_cart", on_click=add_to_cart),
    ),
    state=OrderSG.show_products,
    getter=get_products
)

order_dialog = Dialog(course_window, product_window)
