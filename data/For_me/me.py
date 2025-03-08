from aiogram import types

async def show_my_orders(message: types.Message):
    """
    Заглушка для функціоналу перегляду замовлень.
    Замовлення наразі не підтримуються.
    """
    await message.answer("Функціонал перегляду замовлень наразі недоступний.")
