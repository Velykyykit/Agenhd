import os
import datetime
import asyncio
import gspread
from aiogram import types
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, Cancel, ScrollingGroup
from aiogram_dialog.widgets.text import Const, Format
from aiogram.fsm.state import StatesGroup, State
from fpdf import FPDF

# Конфігурація
SHEET_SKLAD = os.getenv("SHEET_SKLAD")
SHEET_ID = os.getenv("SHEET_ID")
SHEET_ORDER = os.getenv("SHEET_ORDER")
CREDENTIALS_PATH = os.path.join("/app", os.getenv("CREDENTIALS_FILE"))

class OrderSG(StatesGroup):
    select_item = "select_item"
    confirm_order = "confirm_order"

async def get_items(**kwargs):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet("SKLAD")
    data = worksheet.get_all_records()
    return {"items": data}

# Користувач обирає кількість товару через inline кнопки
async def change_quantity(callback: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    cart = manager.dialog_data.setdefault("cart", {})
    cart[item_id] = cart.get(item_id, 0) + (1 if callback.data == "plus" else -1)
    if cart[item_id] < 0:
        cart[item_id] = 0

# Створення тимчасового аркуша
async def create_temp_sheet(user_id):
    date_str = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    sheet_name = f"{user_id}_{date_str}"
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ID)
    sh.add_worksheet(title=sheet_name, rows=100, cols=20)
    return sheet

# Видалення тимчасового аркуша
async def delete_temp_sheet(sheet_name):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ID)
    sh.del_worksheet(sh.worksheet(sheet_name))

# Запис замовлення до таблиці
async def save_order_to_main_sheet(order_data):
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet("orders")
    worksheet.append_row(order_data)

# Генерація PDF
from fpdf import FPDF

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

# Основний діалог
class OrderDialog(StatesGroup):
    select_items = "select_items"
    confirm_order = "confirm_order"

async def confirm_order(call: types.CallbackQuery, widget, manager: DialogManager):
    user_id = call.from_user.id
    date = datetime.datetime.now().strftime("%d.%m.%Y")
    sheet = await create_temp_sheet(user_id)

    cart = manager.dialog_data.get("cart", {})
    items_selected = [f"{item_id}:{qty}" for item_id, qty in cart.items() if qty > 0]

    # запис у тимчасовий аркуш
    worksheet = sheet
    total_sum = 0
    for item_id, qty in cart.items():
        worksheet.append_row([item_id, "Назва товару", price, qty, qty * price])  # ці дані беруться з вашого складу

    # Генерація рахунку
    pdf_file = generate_pdf(order_id=user_id, order_data=cart)

    # Запис у головну таблицю
    order_record = [user_id, datetime.datetime.now().strftime("%d.%m.%Y"),
                    datetime.datetime.now().strftime("%H:%M"), "Телефон",
                    "Ім'я", "Адреса", ",".join(cart.keys()),
                    ",".join(str(qty) for qty in cart.values()),
                    sum([item['price'] * qty for item_id, qty in cart.items()]),
                    "Новий", "рахунок.pdf", "накладна.pdf", ""]
    save_order(order_record)

    # Видалення тимчасового аркуша
    await delete_temp_sheet(sheet.title)

    await call.message.answer_document(types.FSInputFile(pdf_file), caption="Ваше замовлення оформлено.")

# Вікно вибору товару
order_dialog = Dialog(
    Window(
        Const("Виберіть товари:"),
        ScrollingGroup(
            Select(
                Format("{item[name]} - {item[price]} грн"),
                items="items",
                id="item_select",
                item_id_getter=lambda item: item["id"],
            ),
            width=1, height=10,
            id="scroll_items"
        ),
        Button(Const("➕"), id="plus", on_click=change_quantity),
        Button(Const("➖"), id="minus", on_click=change_quantity),
        Button(Const("Оформити замовлення"), id="confirm_order", on_click=confirm_order),
        state=OrderDialog.select_items,
        getter=get_items,
    )
)

dialog = Dialog(select_items_window)
