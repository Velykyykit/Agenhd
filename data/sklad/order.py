import asyncio
from typing import Any, Dict

from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Select, Button, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

# Імпортуємо стани (створені для aiogram-dialog)
from data/sklad.states import OrderSG

# Імпортуємо функції з логіки складу
from data.sklad.sklad import get_all_stock
# Функція для зчитування курсів із аркуша "dictionary" (можна адаптувати)
async def get_courses(**kwargs) -> Dict[str, Any]:
    # Для прикладу повертаємо статичний список курсів; в реальному застосуванні зчитайте з Google Sheets
    return {"courses": ["Alphabet", "Baby's Best Start", "Dragon's Fire"]}

# Getter для товарів за обраним курсом
async def get_items(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    course = dialog_manager.dialog_data.get("course")
    all_items = await get_all_stock()
    # Фільтруємо товари, де стовпець "course" співпадає з обраним курсом
    filtered = [item for item in all_items if item["course"] == course]
    return {"items": filtered}

# Вікно 1: Вибір курсу
select_course_window = Window(
    Const("Оберіть курс для замовлення:"),
    Select(
        Format("{item}"),
        id="course_select",
        items="courses",
        on_click=lambda c, w, m, d: m.dialog().switch_to(OrderSG.select_item, data={"course": c.data}),
    ),
    state=OrderSG.select_course,
    getter=get_courses,
)

# Вікно 2: Вибір товару
select_item_window = Window(
    Format("Курс: {dialog_data[course]}\n\nОберіть товар:\n"),
    # Віджет Select показує список товарів із getter get_items
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
        # Після введення зберігаємо кількість у dialog_data
        on_success=lambda c, w, m, d: m.dialog().update_data({"quantity": d}),
    ),
    Button(Const("Далі"), id="next_button", on_click=lambda c, w, m, d: m.dialog().switch_to(OrderSG.confirm_order)),
    state=OrderSG.input_quantity,
)

# Вікно 4: Підтвердження замовлення
# Тут відображається підсумок замовлення: курс, назва товару, кількість, ціна за одиницю.
# При натисканні кнопки "Підтвердити замовлення" дані потрібно зберегти (наприклад, у orders_store).
async def on_confirm_order(c, w, m, data: Dict[str, Any]):
    # Формуємо підсумкове повідомлення
    order_text = (
        f"Підтвердження замовлення:\n"
        f"Курс: {data.get('course')}\n"
        f"Товар: {data.get('item')[ 'name' ]}\n"
        f"Кількість: {data.get('quantity')}\n"
        f"Ціна за одиницю: {data.get('item')[ 'price' ]}₴\n\n"
        "Натисніть 'Підтвердити замовлення' для збереження замовлення."
    )
    await m.answer(order_text, parse_mode="HTML")
    # Тут можна додати логіку збереження замовлення (наприклад, виклик add_order(user_id, order))
    # Після збереження завершуємо діалог:
    await m.dialog().done()

confirm_order_window = Window(
    Const("Підтвердіть ваше замовлення."),
    Button(Const("Підтвердити замовлення"), id="confirm_order", on_click=on_confirm_order),
    Cancel(Const("Скасувати")),
    state=OrderSG.confirm_order,
)

# Створюємо діалог, який містить усі вікна
order_dialog = Dialog(
    select_course_window,
    select_item_window,
    input_quantity_window,
    confirm_order_window,
)
