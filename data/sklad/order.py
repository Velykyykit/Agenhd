import os
import time
import gspread
from aiogram import types, Router
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Button, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Підключення до Google Sheets
credentials_json = os.getenv("CREDENTIALS_FILE")
if credentials_json:
    credentials_dict = json.loads(credentials_json)

else:
    raise ValueError("❌ Не знайдено CREDENTIALS_FILE у змінних середовища!")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")

gc = gspread.service_account_from_dict(credentials_dict)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")
worksheet_sklad = sh.worksheet("SKLAD")

CACHE_EXPIRY = 300  # 5 хвилин
cache = {
    "courses": {"data": [], "timestamp": 0},
    "products": {"data": {}, "timestamp": 0}
}

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
    return {"products": products}

async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_course"] = item_id
    await callback.answer(f"✅ Ви обрали курс: {item_id}")
    await manager.next()

async def select_product(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    """При натисканні на товар відкривається вікно вибору кількості"""
    manager.dialog_data["selected_product"] = item_id
    manager.dialog_data["quantity"] = 0  # Початкове значення 0
    await manager.next()

async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, action: str):
    """Зміна кількості товару"""
    quantity = manager.dialog_data.get("quantity", 0)
    if action == "increase":
        quantity += 1
    elif action == "decrease" and quantity > 0:
        quantity -= 1
    manager.dialog_data["quantity"] = quantity
    await callback.answer()
    await manager.show()

async def confirm_selection(callback: types.CallbackQuery, widget, manager: DialogManager):
    """Підтвердження вибору кількості"""
    selected_product = manager.dialog_data.get("selected_product", "❌ Невідомий товар")
    quantity = manager.dialog_data.get("quantity", 0)
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
            on_click=select_product
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
        Button(Format("{dialog_data[quantity]}"), id="quantity_display"),
        Button(Const("➕"), id="increase_quantity", on_click=lambda c, w, m: change_quantity(c, w, m, "increase")),
    ),
    Row(
        Button(Const("✅ Підтвердити"), id="confirm_selection", on_click=confirm_selection),
        Button(Const("🔙 Назад"), id="back_to_products", on_click=lambda c, w, m: m.back()),
    ),
    state=OrderSG.select_quantity
)

order_dialog = Dialog(course_window, product_window, quantity_window)

# === Веб-інтерфейс через FastAPI (залишається без змін) ===
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

web_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# In-memory дані для веб-інтерфейсу:
web_courses = {
    1: {"name": "Курс A"},
    2: {"name": "Курс B"}
}
web_products = {
    1: [
        {"id": 101, "name": "Бургер", "price": 4.99, "img": "https://via.placeholder.com/50"},
        {"id": 102, "name": "Картопля фрі", "price": 1.49, "img": "https://via.placeholder.com/50"}
    ],
    2: [
        {"id": 201, "name": "Піцца", "price": 7.99, "img": "https://via.placeholder.com/50"},
        {"id": 202, "name": "Пончик", "price": 1.99, "img": "https://via.placeholder.com/50"}
    ]
}
web_cart = {}  # In-memory "кошик" для веб-інтерфейсу

@web_router.get("/", response_class=HTMLResponse)
def order_index(request: Request):
    return templates.TemplateResponse("order_index.html", {"request": request, "courses": web_courses})

@web_router.get("/course/{course_id}", response_class=HTMLResponse)
def course_page(request: Request, course_id: int):
    items = web_products.get(course_id, [])
    cart_items = {item["id"]: web_cart.get(item["id"], 0) for item in items}
    course_name = web_courses.get(course_id, {}).get("name", "Невідомий курс")
    return templates.TemplateResponse("order_course.html", {
        "request": request,
        "course_id": course_id,
        "course_name": course_name,
        "items": items,
        "cart_items": cart_items
    })

@web_router.post("/update_cart", response_class=HTMLResponse)
def update_cart(request: Request, course_id: int = Form(...), item_id: int = Form(...), action: str = Form(...)):
    current_qty = web_cart.get(item_id, 0)
    if action == "plus":
        current_qty += 1
    elif action == "minus" and current_qty > 0:
        current_qty -= 1
    web_cart[item_id] = current_qty
    items = web_products.get(course_id, [])
    cart_items = {item["id"]: web_cart.get(item["id"], 0) for item in items}
    course_name = web_courses.get(course_id, {}).get("name", "Невідомий курс")
    return templates.TemplateResponse("order_course.html", {
        "request": request,
        "course_id": course_id,
        "course_name": course_name,
        "items": items,
        "cart_items": cart_items
    })

@web_router.post("/confirm", response_class=HTMLResponse)
def confirm_order(request: Request, course_id: int = Form(...)):
    items = web_products.get(course_id, [])
    chosen = []
    for item in items:
        qty = web_cart.get(item["id"], 0)
        if qty > 0:
            chosen.append((item["name"], qty))
    return templates.TemplateResponse("order_confirm.html", {"request": request, "chosen": chosen})

# Експортуємо веб-роутер для FastAPI-додатку
order_router = web_router

# === Роутер для Telegram Mini App (WebApp) ===
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command  # якщо потрібен, але тут ми використовуємо callback

router_catalog = Router()

@router_catalog.callback_query(lambda c: c.data == "order")
async def open_order_webapp(call: types.CallbackQuery):
    await call.answer()
    # Вкажіть URL вашого веб-інтерфейсу, де розміщено Web App (HTTPS!)
    web_app_url = "https://velykyykit.github.io/telegram-mini-app/"  # Замініть на ваш URL, якщо потрібно
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Зробити замовлення", web_app=WebAppInfo(url=web_app_url))]
    ])
    await call.message.answer("Натисніть кнопку нижче, щоб зробити замовлення:", reply_markup=keyboard)
