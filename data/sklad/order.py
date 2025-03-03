import asyncio
from typing import Any, Dict

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Select, Button, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

from data.sklad.states import OrderSG
from data.sklad.sklad import get_all_stock

async def get_courses(**kwargs) -> Dict[str, Any]:
    """Зчитуємо назви курсів (аркуш 'dictionary'). 
       Тут для прикладу статичний список."""
    return {"courses": ["Alphabet", "Baby's Best Start", "Dragon's Fire"]}

async def get_items(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    """Зчитуємо товари (аркуш 'SKLAD'), фільтруємо за обраним курсом."""
    course = dialog_manager.dialog_data.get("course")
    all_items = await get_all_stock()
    filtered = [item for item in all_items if item["course"] == course]
    return {"items": filtered}

# Вікно 1: Вибір курсу
select_course_window = Window(
    Const("Оберіть курс для замовлення:"),
    Select(
        Format("{item}"),
        id="course_select",
        items="courses",
        # Додаємо item_id_getter, щоб уникнути помилки Missing argument
        item_id_getter=lambda x: x, 
        on_click=lambda c, w, m, d: m.dialog().switch_to(OrderSG.select_item, data={"course": c.data}),
    ),
    state=OrderSG.select_course,
    getter=get_courses,
)

# Вікно 2: Вибір товару
select_item_window = Window(
    Format("Курс: {dialog_data[course]}\n\nОберіть товар:\n"),
    Select(
        Format("{item[name]} (Ціна: {item[price]}₴)"),
        id="item_select",
        items="items",
        item_id_getter=lambda item: item["id"],
        on_click=lambda c, w, m, d: m.dialog().switch_to(OrderSG.input_quantity, data={"item": c.data}),
    ),
    state=OrderSG.select_item,
    getter=get_items,
)

# Вікно 3: Введення кількості
input_quantity_window = Window(
    Const("Введіть кількість замовлення для обраного товару:"),
    TextInput(
        id="quantity_input",
        on_success=lambda c, w, m, d: m.dialog().update_data({"quantity": d}),
    ),
    Button(
        Const("Далі"),
        id="next_button",
        on_click=lambda c, w, m, d: m.dialog().switch_to(OrderSG.confirm_order)
    ),
    state=OrderSG.input_quantity,
)

async def on_confirm_order(c, w, m, data: Dict[str, Any]):
    """
    Підтвердження замовлення:
    Відображаємо підсумок (курс, товар, кількість, ціна).
    Далі можна зберегти замовлення і закрити діалог.
    """
    order_text = (
        f"Підтвердження замовлення:\n"
        f"Курс: {data.get('course')}\n"
        f"Товар: {data.get('item')['name']}\n"
        f"Кількість: {data.get('quantity')}\n"
        f"Ціна за одиницю: {data.get('item')['price']}₴\n\n"
        "Натисніть 'Підтвердити замовлення' для збереження."
    )
    await m.answer(order_text, parse_mode="HTML")
    # Тут можна викликати add_order(...) і зберегти замовлення
    await m.dialog().done()

# Вікно 4: Підтвердження замовлення
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
