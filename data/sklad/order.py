from aiogram import Bot, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery
from menu.keyboards import get_restart_keyboard
from data.sklad.sklad import show_courses_for_order

# Оголошення FSM для замовлення
class OrderForm(StatesGroup):
    waiting_for_course = State()
    waiting_for_quantity = State()

async def handle_order_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обробляє callback "order":
    - показує список курсів для замовлення,
    - встановлює стан очікування вибору курсу.
    """
    await call.answer()
    await show_courses_for_order(bot, call.message)
    await state.set_state(OrderForm.waiting_for_course)

async def process_course_selection(call: CallbackQuery, state: FSMContext):
    """
    Обробляє callback, який починається з "course_":
    - зберігає вибір курсу,
    - переводить користувача у стан очікування введення кількості.
    """
    selected_course = call.data[len("course_"):]
    await call.answer(f"Ви обрали: {selected_course}")
    await state.update_data(course=selected_course)
    await call.message.answer("Введіть кількість замовлення:")
    await state.set_state(OrderForm.waiting_for_quantity)

async def process_quantity(message: types.Message, state: FSMContext, get_main_menu_func):
    """
    Обробляє повідомлення з кількістю замовлення:
    - підтверджує замовлення,
    - очищує стан та повертає користувача до головного меню.
    """
    quantity = message.text
    data = await state.get_data()
    selected_course = data.get("course", "Невідомо")
    await message.answer(
        f"Ви замовляєте {quantity} одиниць курсу {selected_course}. Дякуємо за замовлення!"
    )
    await state.clear()
    main_menu = get_main_menu_func()
    await message.answer("📌 Оберіть розділ:", reply_markup=main_menu)
    restart_keyboard = await get_restart_keyboard()
    await message.answer("🔄 Якщо хочете повернутися назад, натисніть кнопку:", reply_markup=restart_keyboard)

def register_order_handlers(router, get_main_menu_func):
    """
    Реєструє обробники процесу замовлення у роутері.
    get_main_menu_func — функція, яка повертає головне меню.
    """
    # Обробник callback для кнопки "order"
    router.callback_query.register(
        lambda call, state, bot: handle_order_callback(call, state, bot),
        F.data == "order"
    )
    # Обробник callback для вибору курсу (починається з "course_")
    router.callback_query.register(
        process_course_selection,
        lambda call: call.data.startswith("course_")
    )
    # Обробник для введення кількості (для стану waiting_for_quantity)
    router.message.register(
        lambda message, state: process_quantity(message, state, get_main_menu_func),
        OrderForm.waiting_for_quantity
    )
