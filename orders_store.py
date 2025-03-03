orders_store = {}  # user_id -> list of orders

def add_order(user_id: int, order: dict):
    """Додає замовлення користувача."""
    if user_id not in orders_store:
        orders_store[user_id] = []
    orders_store[user_id].append(order)

def get_orders(user_id: int):
    """Повертає список замовлень користувача."""
    return orders_store.get(user_id, [])
