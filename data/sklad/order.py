import os
import datetime
import asyncio
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, Cancel, Row, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State
from fpdf import FPDF

# Конфігурація
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_ORDER = os.getenv("SHEET_ORDER")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))
IMG_PATH = "data/sklad/img"

class OrderDialog(StatesGroup):
    select_course = State()
    select_items = State()
    confirm_order = State()

async def get_courses(**kwargs):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("dictionary")
    courses = worksheet.get_all_records(numericise_ignore=['all'], head=1)
    formatted_courses = [
        {"name": course.get("course"), "short": course.get("short")} for course in courses
    ]
    return formatted_courses

async def get_courses_in_columns(**kwargs):
    courses = await get_courses()
    left_column = courses[:10]  # перші 10 курсів
    right_column = courses[10:] # наступні 10 курсів
    return {"left_courses": left_column, "right_courses": right_column}

async def get_items(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course")
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("SKLAD")
    data = worksheet.get_all_records(numericise_ignore=['all'], head=1)
    items = [
        {"id": item["ID"], "name": item["Name"], "price": item["Price"], "quantity": 0}
        for item in data if item["Course"] == selected_course
    ]
    return {"items": items}

async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str, change: int):
    cart = manager.dialog_data.setdefault("cart", {})
    cart[item_id] = max(0, cart.get(item_id, 0) + change)
    await manager.refresh()

order_dialog = Dialog(
    Window(
        Const("📚 Оберіть курс:"),
        Row(
            Column(
                Select(
                    Format("🎓 {item[name]}"), items="left_courses", id="left_course_select",
                    item_id_getter=lambda item: item["short"],
                    on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
                ),
            ),
            Column(
                Select(
                    Format("🎓 {item[name]}"), items="right_courses", id="right_course_select",
                    item_id_getter=lambda item: item["short"],
                    on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
                ),
            ),
        ),
        state=OrderDialog.select_course,
        getter=get_courses_in_columns,
    ),
    Window(
        Const("🛍️ Оберіть товари:"),
        Column(
            Select(
                Format("🏷️ {item[name]} - 💰 {item[price]} грн | 🛒 {item[quantity]}"),
                items="items", id="select_items",
                item_id_getter=lambda item: item["id"],
                on_click=lambda c, w, m, item_id: change_quantity(c, w, m, item_id, 1)
            )
        ),
        Button(Const("✅ Оформити замовлення"), id="confirm_order", on_click=lambda c, w, m: m.switch_to(OrderDialog.confirm_order)),
        state=OrderDialog.select_items,
        getter=get_items,
    )
)
