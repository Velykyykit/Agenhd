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

# Кешування даних
CACHE_EXPIRY = 300  # 5 хвилин
cache = {
    "courses": {"data": [], "timestamp": 0},
    "products": {}  # Структура: { selected_course: {"data": [...], "timestamp": ...} }
}

# Стан діалогу
class OrderSG(StatesGroup):
    select_course = State()
    show_products = State()

# Геттер для курсів
async def get_courses(**kwargs):
    now = time.time()
    if now - cache["courses"]["timestamp"] < CACHE_EXPIRY:
        return {"courses": cache["courses"]["data"]}
    rows = worksheet_courses.get_all_records()
    courses = [{"name": row["course"], "short": row["short"]} for row in rows][:20]
    cache["courses"] = {"data": courses, "timestamp": now}
    return {"courses": courses}

# Геттер для товарів обраного курсу
async def get_products(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course")
    if not selected_course:
        return {"products": []}
    now = time.time()
    if (selected_course in cache["products"] and 
        now - cache["products"][selected_course]["timestamp"] < CACHE_EXPIRY):
        products = cache["products"][selected_course]["data"]
    else:
        rows = worksheet_sklad.get_all_records()
        products = [
            {"id": str(index), "name": row["name"], "price": row["price"]}
            for index, row in enumerate(rows, start=1)
            if row["course"] == selected_course
        ]
        cache["products"][selected_course] = {"data": products, "timestamp": now}
    
    # Ініціалізуємо словник з кількостями для кожного товару
    if "quantities" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["quantities"] = {prod["id"]: 0 for prod in products}
    else:
        for prod in products:
            if prod["id"] not in dialog_manager.dialog_data["quantities"]:
                dialog_manager.dialog_data["quantities"][prod["id"]] = 0

    # За бажанням – можна встановити перший товар як вибраний за замовчуванням
    if products and "selected_product" not in dialog_manager.dialog_data:
        dialog_manager.dialog_data["selected_product"] = products[0]["id"]

    dialog_manager.dialog_data["products"] = products
    return {"products": products}

# Обробка вибору курсу
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_course"] = item_id
    await callback.answer(f"✅ Ви обрали курс: {item_id}")
    await manager.next()

# Функція для зміни кількості для конкретного товару
async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, action: str, product_id: str):
    quantities = manager.dialog_data.get("quantities", {})
    current = quantities.get(product_id, 0)
    if action == "increase":
        current += 1
    elif action == "decrease" and current > 0:
        current -= 1
    quantities[product_id] = current
    manager.dialog_data["quantities"] = quantities
    await callback.answer()
    await manager.show()  # Оновлення вікна

# Підтвердження замовлення – збираємо назви товарів з їх кількістю
async def confirm_selection(callback: types.CallbackQuery, widget, manager: DialogManager):
    quantities = manager.dialog_data.get("quantities", {})
    products = manager.dialog_data.get("products", [])
    message_lines = []
    for prod in products:
        prod_id = prod["id"]
        qty = quantities.get(prod_id, 0)
        if qty > 0:
            message_lines.append(f"{prod['name']}: {qty} шт.")
    message = "\n".join(message_lines) if message_lines else "Немає вибраних товарів."
    await callback.answer(f"Ваше замовлення:\n{message}")
    await manager.done()

# Вікно вибору курсу (Select для списку курсів)
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

# Вікно з товарами: кожен товар відображається як окремий рядок із кнопками «➖», відображенням кількості та «➕»
product_window = Window(
    Format("📦 Товари курсу {dialog_data.selected_course if dialog_data.get('selected_course') else '❓Не вибрано'}:"),
    ScrollingGroup(
        Row(
            # Інформація про товар
            Format("{item[name]} - {item[price]} грн"),
            # Кнопка зменшення
            Button(
                Const("➖"),
                id="minus",
                on_click=lambda c, w, m, item: change_quantity(c, w, m, "decrease", item["id"])
            ),
            # Відображення поточної кількості
            Button(
                Format("{dialog_data.quantities[item[id]]}"),
                id="display"
            ),
            # Кнопка збільшення
            Button(
                Const("➕"),
                id="plus",
                on_click=lambda c, w, m, item: change_quantity(c, w, m, "increase", item["id"])
            )
        ),
        items="products",
        id="products_scroller",
        width=1,
        height=10,
        hide_on_single_page=True
    ),
    Row(
        Button(Const("🔙 Назад"), id="back", on_click=lambda c, w, m: m.back()),
        Button(Const("🛒 Замовити"), id="order", on_click=confirm_selection)
    ),
    state=OrderSG.show_products,
    getter=get_products
)

order_dialog = Dialog(course_window, product_window)
