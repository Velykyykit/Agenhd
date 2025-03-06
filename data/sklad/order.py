import logging
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Select, Button, Row
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.manager.manager import DialogManager
from aiogram import types

logger = logging.getLogger(__name__)

# Дві таблиці Google Sheets
SHEET_DICTIONARY = "dictionary"
SHEET_SKLAD = "SKLAD"

async def change_quantity(c: types.CallbackQuery, w, m: DialogManager, item_id, change):
    """Зміна кількості товару"""
    pass

async def confirm_order(c: types.CallbackQuery, w, m: DialogManager):
    """Підтвердження замовлення"""
    pass

async def get_courses(dialog_manager: DialogManager, **kwargs):
    """Отримання списку курсів"""
    courses = await dialog_manager.middleware_data["gspread_client"].get_data(SHEET_DICTIONARY)
    return {"courses": [{"name": course["course"], "short": course["short"]} for course in courses[:20]]}  # Не більше 20 курсів

async def get_items(dialog_manager: DialogManager, **kwargs):
    """Отримання списку товарів для вибраного курсу"""
    selected_course = dialog_manager.dialog_data.get("selected_course")
    logger.debug(f"[DEBUG] Отримано курс: {selected_course}")
    if not selected_course:
        return {"items": []}
    
    sklad = await dialog_manager.middleware_data["gspread_client"].get_data(SHEET_SKLAD)
    items = [row for row in sklad if row["course"] == selected_course]
    logger.debug(f"[DEBUG] Знайдено {len(items)} товарів для курсу {selected_course}")
    return {"items": items}

order_dialog = Dialog(
    Window(
        Const("\ud83d\udcda Оберіть курс:"),
        Select(
            text=lambda item: f"\ud83c\udf93 {item['name']}",
            id="select_course",
            item_id_getter=lambda item: item["short"],
            on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to("OrderDialog:select_items")
        ),
        state="OrderDialog:select_course",
        getter=get_courses  # Виклик `get_courses`
    ),
    Window(
        Const("\ud83d\uded9️ Оберіть товари:"),
        Row(
            Select(
                text=lambda item: f"➕ {item['name']}",
                id="select_item",
                item_id_getter=lambda item: item["id"],
                on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, +1)
            )
        ),
        Button(Const("✅ Оформити замовлення"), id="confirm_order", on_click=confirm_order),
        state="OrderDialog:select_items",
        getter=get_items  # Виклик `get_items`
    )
)
