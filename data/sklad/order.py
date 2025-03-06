import logging
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Select, Button, Row
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.manager.manager import DialogManager
from aiogram_dialog.api.exceptions import InvalidWidgetIdError
from aiogram import types

logger = logging.getLogger(__name__)

# Дві таблиці Google Sheets
SHEET_DICTIONARY = "dictionary"
SHEET_SKLAD = "SKLAD"

async def get_courses(dialog_manager: DialogManager):
    """Отримання списку курсів"""
    courses = await dialog_manager.middleware_data["gspread_client"].get_data(SHEET_DICTIONARY)
    return [{"name": course["course"], "short": course["short"]} for course in courses[:20]]  # Не більше 20 курсів

async def get_items(dialog_manager: DialogManager):
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
        Const("📚 Оберіть курс:"),
        Select(
            text=lambda item: f"🎓 {item['name']}",
            id="select_course",
            item_id_getter=lambda item: item["short"],
            items=await get_courses(DialogManager()),
            on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
        ),
        state="OrderDialog:select_course",
    ),
    Window(
        Const("🛍️ Оберіть товари:"),
        Row(
            *[
                Button(
                    Const(f"➕ {item['name']}"),
                    id=f"add_{item['id']}",
                    on_click=lambda c, w, m, item_id=item["id"]: change_quantity(c, w, m, item_id, +1)
                ) for item in (await get_items(DialogManager()))["items"]
            ]
        ),
        Button(Const("✅ Оформити замовлення"), id="confirm_order", on_click=confirm_order),
        state="OrderDialog:select_items",
    )
)

def change_quantity(c: types.CallbackQuery, w, m: DialogManager, item_id, change):
    """Зміна кількості товару"""
    pass

def confirm_order(c: types.CallbackQuery, w, m: DialogManager):
    """Підтвердження замовлення"""
    pass
