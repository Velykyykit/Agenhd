from aiogram.fsm.state import StatesGroup, State

class OrderSG(StatesGroup):
    select_course = State()
    select_item = State()
    input_quantity = State()
    confirm_order = State()
