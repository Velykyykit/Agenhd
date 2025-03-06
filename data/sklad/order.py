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
        {"name": course["A"], "short": course["B"]} for course in courses
    ]
    return {"courses": formatted_courses}

async def get_courses_in_columns(**kwargs):
    data = await get_courses()
    courses = data["courses"]
    left_column = courses[:10]  # перші 10 курсів
    right_column = courses[10:] # наступні 10 курсів
    return {"left_courses": left_column, "right_courses": right_column}

order_dialog = Dialog(
    Window(
        Const("📚 Оберіть курс:"),
        Row(
            Column(
                Select(
                    Format("🎓 {item[name]}"), items="left_courses", id="left_course_select",
                    item_id_getter=lambda item: item["short"], on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
                ),
            ),
            Column(
                Select(
                    Format("🎓 {item[name]}"), items="right_courses", id="right_course_select",
                    item_id_getter=lambda item: item["short"], on_click=lambda c, w, m, item_id: m.dialog_data.update(selected_course=item_id) or m.switch_to(OrderDialog.select_items)
                ),
            ),
        ),
        state=OrderDialog.select_course,
        getter=get_courses_in_columns,
    )
)
