import os
import gspread
import logging
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Button, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State

# Логування для Railway
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

# Отримання товарів із вибраного курсу
async def get_products(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course", None)
    if not selected_course:
        return {"products": []}

    rows = worksheet_sklad.get_all_records()
    products = [
        {
            "id": row["id"],
            "name": row["name"],
            "price": row["price"],
            "quantity": dialog_manager.dialog_data.get(f"quantity_{row['id']}", 0)  # Стартова кількість = 0
        }
        for row in rows if row["course"] == selected_course
    ]

    return {"products": products}

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_course"] = item_id
    logging.info(f"[COURSE SELECTED] Користувач {callback.from_user.id} обрав курс: {item_id}")
    await callback.answer(f"✅ Ви обрали курс: {item_id}")
    await manager.next()

# Обробник зміни кількості товару
async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str, delta: int):
    current_quantity = manager.dialog_data.get(f"quantity_{item_id}", 0)
    new_quantity = max(0, current_quantity + delta)  # Значення не може бути нижче 0
    manager.dialog_data[f"quantity_{item_id}"] = new_quantity

    logging.info(f"[QUANTITY UPDATED] Товар {item_id}: {current_quantity} -> {new_quantity}")
    await callback.answer(f"🆕 Кількість: {new_quantity}")

    # Оновлення діалогу (щоб змінена кількість з'явилася в повідомленні)
    await manager.dialog().show()

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

# Вікно вибору товарів
product_window = Window(
    Format("📦 Товари курсу {dialog_data[selected_course]}:"),
    ScrollingGroup(
        Row(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн"),
            Button(Const("➖"), id=lambda item: f"minus_{item['id']}",
                   on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, -1)),
            Format("🔢 {item[quantity]} шт"),
            Button(Const("➕"), id=lambda item: f"plus_{item['id']}",
                   on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, +1)),
        ),
        items="products",
        id="products_scroller",
        width=1,
        height=10,
        hide_on_single_page=True  
    ),
    Button(Const("✅ Готово"), id="confirm_order", on_click=lambda c, w, m: c.answer("🔄 Оформлення замовлення...")),
    Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
    state=OrderSG.show_products,
    getter=get_products
)

# Створюємо діалог
order_dialog = Dialog(course_window, product_window)
