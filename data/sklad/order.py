import os
import asyncio
import gspread

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Button, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput
from aiogram.fsm.state import StatesGroup, State
from aiogram import types

from data.sklad.sklad import get_all_stock

class OrderSG(StatesGroup):
    select_course = State()
    select_item = State()
    input_quantity = State()
    confirm_order = State()

async def get_courses(**kwargs):
    ...
    return {"courses": data}

async def get_items(dialog_manager: DialogManager, **kwargs):
    ...
    return {"items": filtered}

async def on_course_selected(call: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    manager.dialog_data["course"] = item_id
    await manager.switch_to(OrderSG.select_item)

async def on_item_selected(call: types.CallbackQuery, widget, manager: DialogManager, item_id: str):
    ...

async def on_next_quantity(call: types.CallbackQuery, widget, manager: DialogManager):
    ...

async def on_confirm_order(call: types.CallbackQuery, widget, manager: DialogManager):
    ...

select_course_window = Window(
    Const("Оберіть курс для замовлення:"),
    # Замість Select(...) напряму - обгортка ScrollingGroup
    ScrollingGroup(
        Select(
            Format("{item}"),
            id="course_select",
            items="courses",
            item_id_getter=lambda x: x,
            on_click=on_course_selected,
        ),
        width=1,   # одна кнопка в рядку
        height=10, # 10 кнопок за раз
        id="scroll_courses"
    ),
    state=OrderSG.select_course,
    getter=get_courses,
)

select_item_window = Window(
    Format("Курс: {dialog_data[course]}\n\nОберіть товар:\n"),
    ScrollingGroup(
        Select(
            Format("{item[name]} (Ціна: {item[price]}₴)"),
            id="item_select",
            items="items",
            item_id_getter=lambda item: item["id"],
            on_click=on_item_selected,
        ),
        width=1,
        height=10,
        id="scroll_items"
    ),
    state=OrderSG.select_item,
    getter=get_items,
)

# решта (input_quantity_window, confirm_order_window) без змін

order_dialog = Dialog(
    select_course_window,
    select_item_window,
    input_quantity_window,
    confirm_order_window,
)
