from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Select, Button, Cancel
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
    return {"courses": ["Alphabet", "Baby's Best Start", "Dragon's Fire"]}

async def get_items(dialog_manager: DialogManager, **kwargs):
    course = dialog_manager.dialog_data.get("course")
    all_items = await get_all_stock()
    return {"items": [item for item in all_items if item["course"] == course]}

async def on_course_selected(
    call: types.CallbackQuery,
    widget,
    manager: DialogManager,
    item_id: str
):
    """Обробка вибору курсу."""
    manager.dialog_data["course"] = item_id
    await manager.switch_to(OrderSG.select_item)

async def on_item_selected(
    call: types.CallbackQuery,
    widget,
    manager: DialogManager,
    item_id: str
):
    """Обробка вибору товару."""
    all_items = await get_all_stock()
    item = next((i for i in all_items if i["id"] == item_id), None)
    manager.dialog_data["item"] = item
    await manager.switch_to(OrderSG.input_quantity)

select_course_window = Window(
    Const("Оберіть курс для замовлення:"),
    Select(
        Format("{item}"),
        id="course_select",
        items="courses",
        item_id_getter=lambda x: x,
        on_click=on_course_selected,
    ),
    state=OrderSG.select_course,
    getter=get_courses,
)

select_item_window = Window(
    Format("Курс: {dialog_data[course]}\n\nОберіть товар:\n"),
    Select(
        Format("{item[name]} (Ціна: {item[price]}₴)"),
        id="item_select",
        items="items",
        item_id_getter=lambda item: item["id"],
        on_click=on_item_selected,
    ),
    state=OrderSG.select_item,
    getter=get_items,
)

async def on_next_quantity(
    call: types.CallbackQuery,
    widget,
    manager: DialogManager,
):
    """Натискання кнопки «Далі» після введення кількості."""
    await manager.switch_to(OrderSG.confirm_order)

input_quantity_window = Window(
    Const("Введіть кількість замовлення для обраного товару:"),
    TextInput(
        id="quantity_input",
        on_success=lambda c, w, m, txt: m.dialog_data.update({"quantity": txt}),
    ),
    Button(Const("Далі"), id="next_button", on_click=on_next_quantity),
    state=OrderSG.input_quantity,
)

async def on_confirm_order(
    call: types.CallbackQuery,
    widget,
    manager: DialogManager,
):
    data = manager.dialog_data
    order_text = (
        f"Підтвердження замовлення:\n"
        f"Курс: {data.get('course')}\n"
        f"Товар: {data.get('item')['name']}\n"
        f"Кількість: {data.get('quantity')}\n"
        f"Ціна за одиницю: {data.get('item')['price']}₴\n\n"
        "Натисніть 'Підтвердити замовлення' для збереження."
    )
    await call.message.answer(order_text, parse_mode="HTML")
    # Тут можна викликати add_order(...)
    await manager.done()

confirm_order_window = Window(
    Const("Підтвердіть ваше замовлення."),
    Button(Const("Підтвердити замовлення"), id="confirm_order", on_click=on_confirm_order),
    Cancel(Const("Скасувати")),
    state=OrderSG.confirm_order,
)

order_dialog = Dialog(
    select_course_window,
    select_item_window,
    input_quantity_window,
    confirm_order_window,
)
