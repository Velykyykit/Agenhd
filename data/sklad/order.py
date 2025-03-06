# Вікно виводу товарів
product_window = Window(
    Format("📦 Товари курсу {dialog_data[selected_course]}:"),

    Group(
        Select(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн | 📦 {dialog_data[cart].get(item[id], 0)} шт"),
            items="products",
            id="product_select",
            item_id_getter=lambda item: str(item["id"]),
        ),
        width=1,
        id="products_group"
    ),

    Group(
        Button(Const("➖"), id="minus_button", on_click=update_quantity),
        Button(Const("➕"), id="plus_button", on_click=update_quantity),
        width=2  # Два стовпці для + та -
    ),

    Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
    Button(Const("🛒 Додати в кошик"), id="add_to_cart", on_click=lambda c, w, m: c.answer("🔹 Заглушка: Додано в кошик")),
    
    state=OrderSG.show_products,
    getter=get_products
)
