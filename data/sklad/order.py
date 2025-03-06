import os
import gspread
import logging
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Button, Row
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
    selected_course = dialog_manager.dialog_data.get("selected_course", None)
    cart = dialog_manager.dialog_data.setdefault("cart", {})

    if not selected_course:
        return {"products": []}

    rows = worksheet_sklad.get_all_records()
    products = [
        {"id": row["id"], "name": row["name"], "price": row["price"], "quantity": cart.get(str(row["id"]), 0)}
        for row in rows if row["course"] == selected_course
    ]

    return {"products": products}

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    selected_course = item_id
    manager.dialog_data["selected_course"] = selected_course
    manager.dialog_data["cart"] = {}

    # 🔥 Логування Railway
    logging.info(f"[COURSE SELECTED] Користувач {callback.from_user.id} обрав курс: {selected_course}")

    await callback.answer(f"✅ Ви обрали курс: {selected_course}")

    # Перехід до списку товарів
    await manager.next()

# Обробники кнопок ➖ та ➕
async def update_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str, delta: int):
    cart = manager.dialog_data.setdefault("cart", {})
    current_quantity = cart.get(item_id, 0)
    new_quantity = max(0, current_quantity + delta)  # Не дозволяємо значення менше 0
    cart[item_id] = new_quantity
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
    Format("📦 Товари курсу {dialog_data[selected_course]}:"),
    ScrollingGroup(
        Row(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн"),
            Button(Const("➖"), id=lambda item: f"minus_{item['id']}",
                   on_click=lambda c, w, m: update_quantity(c, w, m, str(c.data.split("_")[1]), -1)),
            Format("{item[quantity]}"),
            Button(Const("➕"), id=lambda item: f"plus_{item['id']}",
                   on_click=lambda c, w, m: update_quantity(c, w, m, str(c.data.split("_")[1]), 1)),
        ),
        items="products",
        id="products_scroller",
        width=1,
        height=10,
        hide_on_single_page=True
    ),
    Row(
        Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
        Button(Const("🛒 Додати в кошик"), id="add_to_cart", on_click=lambda c, w, m: c.answer("🚧 Функція в розробці")),
    ),
    state=OrderSG.show_products,
    getter=get_products
)
