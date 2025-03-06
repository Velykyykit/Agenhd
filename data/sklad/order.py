import logging
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Select, Button, Row, Column
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.manager.manager import DialogManager
from aiogram import types

logger = logging.getLogger(__name__)

# Дві таблиці Google Sheets
SHEET_DICTIONARY = "dictionary"

async def get_courses(dialog_manager: DialogManager, **kwargs):
    """Отримання списку курсів із таблиці"""
    courses = await dialog_manager.middleware_data["gspread_client"].get_data(SHEET_DICTIONARY)
    courses = [{"name": course["course"], "short": course["short"]} for course in courses[:20]]  # Не більше 20 курсів
    return {"courses": courses}

def log_selected_course(c: types.CallbackQuery, w, m: DialogManager, item_id):
    """Виведення вибраного курсу в дебаг"""
    logger.debug(f"[DEBUG] Обраний курс: {item_id}")
    m.dialog_data.update(selected_course=item_id)
    
order_dialog = Dialog(
    Window(
        Const("📚 Оберіть курс:"),
        Row(
            Column(
                Select(
                    text=lambda item: f"🎓 {item['name']}",
                    id="select_course",
                    item_id_getter=lambda item: item["short"],
                    on_click=log_selected_course,
                    items="courses[:10]"
                )
            ),
            Column(
                Select(
                    text=lambda item: f"🎓 {item['name']}",
                    id="select_course_2",
                    item_id_getter=lambda item: item["short"],
                    on_click=log_selected_course,
                    items="courses[10:]"
                )
            )
        ),
        state="OrderDialog:select_course",
        getter=get_courses  # Виклик функції отримання курсів
    )
)
