from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    Message
)
from aiogram.fsm.state import StatesGroup, State

# Імпортуємо функцію, яка показує курси, і ту, що повертає всі товари
from data.sklad.sklad import show_courses_for_order, get_all_stock

# Імпортуємо клавіатуру перезапуску
from menu.keyboards import get_restart_keyboard

class OrderForm(StatesGroup):
    waiting_for_course = State()
    waiting_for_item = State()
    waiting_for_quantity = State()

async def handle_order_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Користувач натиснув "🛒 Зробити Замовлення".
    1) Виводимо список курсів (з аркуша 'dictionary').
    2) Переходимо у стан waiting_for_course.
    """
    await call.answer()
    # Показуємо список курсів
    await show_courses_for_order(bot, call.message)
    # Установлюємо стан "очікування вибору курсу"
    await state.set_state(OrderForm.waiting_for_course)

async def process_course_selection(call: CallbackQuery, state: FSMContext):
    """
    Користувач обирає курс (callback_data="course_...").
    1) Зберігаємо назву курсу у FSM.
    2) Фільтруємо товари з таблиці 'SKLAD' за цим курсом.
    3) Виводимо інформацію (id, назва, наявність, доступно, ціна) українською.
    4) Показуємо інлайн-кнопки для кожного товару.
    5) Переходимо у стан waiting_for_item.
    """
    selected_course = call.data[len("course_"):]
    await call.answer(f"Ви обрали курс: {selected_course}")
    await state.update_data(course=selected_course)

    # Отримуємо всі товари з таблиці SKLAD
    all_items = await get_all_stock()
    # Фільтруємо за вибраним курсом
    filtered_items = [item for item in all_items if item["course"] == selected_course]

    if not filtered_items:
        await call.message.answer("❌ Немає товарів у цьому курсі.")
        await state.clear()
        return

    # Формуємо текст із детальною інформацією (у HTML)
    text = "Ось товари для цього курсу:<br><br>"
    for item in filtered_items:
            text = "Ось товари для цього курсу:\n\n"
    for item in filtered_items:
        text += (
            f"<b>ID</b>: {item['id']}\n"
            f"<b>Назва</b>: {item['name']}\n"
            f"<b>Наявність</b>: {item['stock']}\n"
            f"<b>Доступно</b>: {item['available']}\n"
            f"<b>Ціна</b>: {item['price']}₴\n\n"
        )

    await call.message.answer(text, parse_mode="HTML")

    # Створюємо інлайн-клавіатуру для вибору товару
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for item in filtered_items:
        # Текст кнопки: "Назва (Ціна₴)"
        button_text = f"{item['name']} ({item['price']}₴)"
        callback_data = f"item_{item['id']}"
        markup.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        ])

    await call.message.answer("Оберіть товар:", reply_markup=markup)
    await state.set_state(OrderForm.waiting_for_item)

async def process_item_selection(call: CallbackQuery, state: FSMContext):
    """
    Користувач обирає товар (callback_data="item_...").
    1) Знаходимо товар у списку SKLAD за ID.
    2) Зберігаємо ID і назву товару в FSM.
    3) Просимо ввести кількість.
    4) Переходимо у стан waiting_for_quantity.
    """
    selected_item_id = call.data[len("item_"):]
    await call.answer(f"Обрано товар ID: {selected_item_id}")

    # Знаходимо товар
    all_items = await get_all_stock()
    item = next((i for i in all_items if i["id"] == selected_item_id), None)
    if not item:
        await call.message.answer("❌ Товар не знайдено.")
        await state.clear()
        return

    # Зберігаємо дані у FSM
    await state.update_data(item_id=selected_item_id, item_name=item["name"])
    await call.message.answer(
        f"Ви обрали: {item['name']}\n"
        "Введіть кількість:"
    )
    await state.set_state(OrderForm.waiting_for_quantity)

async def process_quantity(message: types.Message, state: FSMContext, get_main_menu_func):
    """
    Користувач вводить кількість.
    1) Зчитуємо кількість,
    2) Підтверджуємо замовлення (з курсом і назвою товару),
    3) Повертаємося в головне меню.
    """
    quantity = message.text
    data = await state.get_data()
    course_name = data.get("course", "Невідомо")
    item_name = data.get("item_name", "Невідомо")

    await message.answer(
        f"Ви замовляєте {quantity} одиниць товару '{item_name}' (курс: {course_name}). "
        "Дякуємо за замовлення!"
    )
    await state.clear()

    # Повертаємо головне меню
    main_menu = get_main_menu_func()
    await message.answer("📌 Оберіть розділ:", reply_markup=main_menu)
    restart_keyboard = await get_restart_keyboard()
    await message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=restart_keyboard)

def register_order_handlers(router, get_main_menu_func):
    """
    Реєструє обробники процесу замовлення у роутері.
    """
    # Обгортки для await
    async def order_callback_wrapper(call: CallbackQuery, state: FSMContext, bot: Bot):
        await handle_order_callback(call, state, bot)

    async def course_selection_wrapper(call: CallbackQuery, state: FSMContext):
        await process_course_selection(call, state)

    async def item_selection_wrapper(call: CallbackQuery, state: FSMContext):
        await process_item_selection(call, state)

    async def quantity_wrapper(message: Message, state: FSMContext):
        await process_quantity(message, state, get_main_menu_func)

    # 1) Натискання "🛒 Зробити Замовлення"
    router.callback_query.register(order_callback_wrapper, F.data == "order")

    # 2) Обрання курсу "course_..."
    router.callback_query.register(course_selection_wrapper, lambda call: call.data.startswith("course_"))

    # 3) Обрання товару "item_..."
    router.callback_query.register(item_selection_wrapper, lambda call: call.data.startswith("item_"))

    # 4) Введення кількості
    router.message.register(quantity_wrapper, OrderForm.waiting_for_quantity)
