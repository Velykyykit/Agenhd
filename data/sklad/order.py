import os
import gspread
import logging
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
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
    rows = worksheet_sklad.get_all_records()
    products = [
        {"id": str(row["id"]), "name": row["name"], "price": row["price"]}
        for row in rows if row.get("course") == selected_course
    ]
    return {"products": products, "selected_course": selected_course}

# Обробник вибору курсу
async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_course"] = item_id
    logging.info(f"[COURSE SELECTED] Користувач {callback.from_user.id} обрав курс: {item_id}")
    await callback.answer(f"✅ Ви обрали курс: {item_id}")
    await manager.next()

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
    Format("📦 Товари курсу {selected_course}:"),
    ScrollingGroup(
        Select(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн"),
            items="products",
            id="product_select",
            item_id_getter=lambda item: item["id"],
        ),
        width=1,
        id="products_scroller",
        hide_on_single_page=True
    ),
    state=OrderSG.show_products,
    getter=get_products
)

# Створюємо діалог
order_dialog = Dialog(course_window, product_window)
