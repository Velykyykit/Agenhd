import os
import gspread
import logging
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Button, Group
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Налаштування логування (Railway)
logging.basicConfig(level=logging.INFO)

# Конфігурація Google Sheets
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

# Підключення до Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")
worksheet_sklad = sh.worksheet("SKLAD")

# Стан вибору курсу і товару
class OrderSG(StatesGroup):
    select_course = State()
    show_products = State()

# Отримання курсів (до 20)
async def get_courses(**kwargs):
    rows = worksheet_courses.get_all_records()
    courses = [{"name": row["course"], "short": row["short"]} for row in rows][:20]
    return {"courses": courses}

# Отримання товарів за курсом
async def get_products(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course", "❓Курс не вибрано")
    
    if "cart" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["cart"] = {}
    cart = dialog_manager.dialog_data["cart"]
    
    rows = worksheet_sklad.get_all_records()
    products = [
        {"id": str(row["id"]), "name": row["name"], "price": row["price"]}
        for row in rows if row.get("course") == selected_course
    ]

    return {
        "products": products,
        "selected_course": selected_course,
        "cart": cart,
    }

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    selected_course = item_id
    manager.dialog_data["selected_course"] = selected_course
    if "cart" not in manager.dialog_data:
        manager.dialog_data["cart"] = {}
    logging.info(f"[COURSE SELECTED] Користувач {callback.from_user.id} обрав курс: {selected_course}")
    await callback.answer(f"✅ Ви обрали курс: {selected_course}")
    await manager.next()

# Обробка натискання кнопок + і -
async def update_quantity(callback: types.CallbackQuery, widget, manager: DialogManager):
    if "cart" not in manager.dialog_data:
        manager.dialog_data["cart"] = {}
    cart = manager.dialog_data["cart"]
    action, item_id = callback.data.split("_")  # "plus_123" або "minus_123"
    
    delta = 1 if action == "plus" else -1
    current_quantity = cart.get(item_id, 0)
    new_quantity = max(0, current_quantity + delta)  # Не дозволяємо значення менше 0
    cart[item_id] = new_quantity

    logging.info(f"[UPDATE CART] {callback.from_user.id} змінив кількість {item_id}: {new_quantity}")

    await callback.answer(f"🔄 Кількість оновлено: {new_quantity}")
    await manager.show()  # Оновлення вікна

# Вікно вибору курсу
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

# Вікно виводу товарів
product_window = Window(
    Format("📦 Товари курсу {selected_course}:")
    ,
    ScrollingGroup(
        Select(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн | 📦 {cart.get(item[id], 0) if cart else 0} шт"),
            items="products",
            id="product_select",
            item_id_getter=lambda item: item["id"],
        ),
        width=1,
        id="products_scroller",
        hide_on_single_page=True
    ),

    Group(
        Button(Const("➖"), id="minus_button", on_click=update_quantity),
        Button(Const("➕"), id="plus_button", on_click=update_quantity),
        width=2
    ),

    Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
    Button(Const("🛒 Додати в кошик"), id="add_to_cart", on_click=lambda c, w, m: c.answer("🔹 Заглушка: Додано в кошик")),

    state=OrderSG.show_products,
    getter=get_products
)

# Створюємо діалог
order_dialog = Dialog(course_window, product_window)
