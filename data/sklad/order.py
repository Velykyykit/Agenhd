import os
import datetime
import asyncio
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, Cancel, Grid
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State
from fpdf import FPDF

# Конфігурація
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_ORDER = os.getenv("SHEET_ORDER")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

class OrderDialog(StatesGroup):
    select_course = State()
    select_items = State()
    confirm_order = State()

async def get_courses(**kwargs):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("dictionary")
    courses = worksheet.col_values(1)
    return {"courses": courses}

async def get_items(dialog_manager: DialogManager, **kwargs):
    selected_course = dialog_manager.dialog_data.get("selected_course")
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_SKLAD)
    worksheet = sh.worksheet("SKLAD")
    all_items = worksheet.get_all_records()
    cart = dialog_manager.dialog_data.get("cart", {})
    filtered_items = [
        {"id": str(item["id"]), "name": item["name"], "price": item["price"], "quantity": cart.get(str(item["id"]), 0)}
        for item in all_items if item["course"] == selected_course
    ]
    return {"items": filtered_items}

async def select_course(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_course"] = item_id
    await manager.switch_to(OrderDialog.select_items)

async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    cart = manager.dialog_data.setdefault("cart", {})
    action = 1 if "plus" in callback.data else -1
    cart[item_id] = max(cart.get(item_id, 0) + action, 0)
    await manager.update()

async def create_temp_sheet(user_id):
    date_str = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    sheet_name = f"{user_id}_{date_str}"
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ORDER)
    sheet = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
    return sheet

async def delete_temp_sheet(sheet_name):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ORDER)
    sh.del_worksheet(sh.worksheet(sheet_name))

async def save_order_to_main_sheet(order_data):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ORDER)
    worksheet = sh.worksheet("orders")
    worksheet.append_row(order_data)

# Генерація PDF

def generate_pdf(order_id, order_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Рахунок №{order_id}', ln=True)
    pdf.ln(10)
    for item in order_data:
        pdf.cell(0, 10, f"{item['name']} {item['quantity']} x {item['price']} грн = {item['quantity']*item['price']} грн", ln=True)
    file_name = f"{order_id}.pdf"
    pdf.output(file_name)
    return file_name

async def confirm_order(call: types.CallbackQuery, widget, manager: DialogManager):
    user_id = call.from_user.id
    date = datetime.datetime.now().strftime("%d.%m.%Y")
    sheet = await create_temp_sheet(user_id)

    cart = manager.dialog_data.get("cart", {})

    total_sum = 0
    worksheet = sheet
    for item_id, qty in cart.items():
        worksheet.append_row([item_id, "Назва товару", "Ціна", qty, "Сума"])  # Замінити на реальні дані

    pdf_file = generate_pdf(order_id=user_id, order_data=cart)

    order_record = [user_id, date,
                    datetime.datetime.now().strftime("%H:%M"), "Телефон",
                    "Ім'я", "Адреса", ",".join(cart.keys()),
                    ",".join(str(qty) for qty in cart.values()),
                    total_sum,
                    "Новий", "рахунок.pdf", "накладна.pdf", ""]
    await save_order_to_main_sheet(order_record)

    await delete_temp_sheet(sheet.title)

    await call.message.answer_document(types.FSInputFile(pdf_file), caption="Ваше замовлення оформлено.")

order_dialog = Dialog(
    Window(
        Const("Оберіть курс:"),
        Select(
            Format("{item}"), items="courses", id="course_select",
            item_id_getter=lambda item: item, on_click=select_course
        ),
        state=OrderDialog.select_course,
        getter=get_courses,
    ),
    Window(
        Const("🛒 Виберіть товари:"),
        Grid(
            Select(
                Format("{item[name]} \n 💰 {item[price]} грн \n 🛍 {item[quantity]} шт"),
                items="items",
                id="item_select",
                item_id_getter=lambda item: item["id"],
            ),
            Button(Const("➖"), id="minus", on_click=change_quantity),
            Button(Const("➕"), id="plus", on_click=change_quantity),
            width=3,  # Кількість товарів у ряді
        ),
        Button(Const("🛍 ОФОРМИТИ ЗАМОВЛЕННЯ"), id="confirm_order", on_click=confirm_order),
        state=OrderDialog.select_items,
        getter=get_items,
    )
)
