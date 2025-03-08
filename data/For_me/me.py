from aiogram import types

async def show_my_orders(message: types.Message):
    """
    Відображає список замовлень для користувача.
    Кожне замовлення містить ID товару, назву, кількість, ціну.
    """
    user_id = message.from_user.id
    orders = get_orders(user_id)
    if not orders:
        await message.answer("Ви ще не зробили жодного замовлення.")
    else:
        text = "Ваші замовлення:\n\n"
        for idx, order in enumerate(orders, 1):
            text += (
                f"<b>Замовлення {idx}:</b>\n"
                f"ID товару: {order.get('item_id', 'N/A')}\n"
                f"Назва: {order.get('item', 'N/A')}\n"
                f"Кількість: {order.get('quantity', 'N/A')}\n"
                f"Ціна: {order.get('price', 'N/A')}₴\n\n"
            )
        await message.answer(text, parse_mode="HTML")
