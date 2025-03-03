from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    Message
)
from aiogram.fsm.state import StatesGroup, State

from data.sklad.sklad import show_courses_for_order, get_all_stock
from menu.keyboards import get_restart_keyboard

# Оголошення FSM для замовлення
class OrderForm(StatesGroup):
    waiting_for_course = State()
    waiting_for_item = State()
    waiting_for_quantity = State()

async def handle_order_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
    """
    1) Користувач натиснув "🛒 Зробити Замовлення".
    2) Показуємо список курсів (із аркуша 'dictionary').
    3) Переходимо у стан waiting_for_course.
    """
    await call.answer()
    # Показуємо список курсів
    await show_courses_for_order(bot, call.message)
    # Встановлюємо стан
    await state.set_state(OrderForm.waiting_for_course)

async def process_course_selection(call: CallbackQuery, state: FSMContext):
    """
    1) Користувач обрав курс (callback_data="course_...").
    2) Зберігаємо вибраний курс у FSM.
    3) Виводимо список товарів із аркуша 'SKLAD', де course == обраний курс,
       із детальною інформацією (Назва, Наявність, Доступно, Ціна).
    4) Відправляємо інлайн-клавіатуру для вибору товару.
    5) Переходимо у стан waiting_for_item.
    """
    selected_course = call.data[len("course_"):]
    await call.answer(f"Ви обрали курс: {selected_course}")
    await state.update_data(course=selected_course)

    # Отримуємо усі товари
    all_items = await get_all_stock()
    # Фільтруємо за обраним курсом
    filtered_items = [item for item in all_items if item["course"] == selected_course]

    if not filtered_items:
        await call.message.answer("❌ Немає товарів у цьому курсі.")
        await state.clear()
        return

    # Формуємо повідомлення з інформацією про товари
    text = "Ось товари для цього курсу:\n\n"
    for item in filtered_items:
        text += (
            f"**ID**: {item['id']}\n"
            f"**Назва**: {item['name']}\n"
            f"**Наявність на складі**: {item['stock']}\n"
            f"**Доступно для замовлення**: {item['available']}\n"
            f"**Ціна за 1 штуку**: {item['price']}₴\n\n"
        )

    await call.message.answer(text, parse_mode="Markdown")

    # Створюємо інлайн-клавіатуру з товарами
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for item in filtered_items:
        # Текст кнопки, наприклад: "Alphabet answer Book 1 (100₴)"
        button_text = f"{item['name']} ({item['price']}₴)"
        markup.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"item_{item['id']}")
        ])

    await call.message.answer("Оберіть товар:", reply_markup=markup)
    await state.set_state(OrderForm.waiting_for_item)

async def process_item_selection(call: CallbackQuery, state: FSMContext):
    """
    1) Користувач обрав товар (callback_data="item_...").
    2) Зберігаємо ID товару та назву у FSM.
    3) Просимо ввести кількість.
    4) Переходимо у стан waiting_for_quantity.
    """
    selected_item_id = call.data[len("item_"):]
    await call.answer(f"Обрано товар ID: {selected_item_id}")

    # Шукаємо товар у загальному списку
    all_items = await get_all_stock()
    item = next((i for i in all_items if i["id"] == selected_item_id), None)
    if not item:
        await call.message.answer("❌ Товар не знайдено. Спробуйте ще раз.")
        await state.clear()
        return

    # Зберігаємо у FSM
    await state.update_data(item_id=selected_item_id, item_name=item["name"])
    await call.message.answer(
        f"Ви обрали: {item['name']}\nВведіть кількість:"
    )
    await state.set_state(OrderForm.waiting_for_quantity)

async def process_quantity(message: Message, state: FSMContext, get_main_menu_func):
    """
    1) Користувач вводить кількість.
    2) Зберігаємо кількість, підтверджуємо замовлення.
    3) Повертаємося до головного меню.
    """
    quantity = message.text
    data = await state.get_data()
    course_name = data.get("course", "Невідомо")
    item_name = data.get("item_name", "Невідомо")

    await message.answer(
        f"Ви замовляєте {quantity} одиниць товару '{item_name}' "
        f"(курс: {course_name}). Дякуємо за замовлення!"
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
    # Асинхронні обгортки, щоб викликати функції з await
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
