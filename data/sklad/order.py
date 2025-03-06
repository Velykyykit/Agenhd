product_window = Window(
    Format("📦 Товари курсу {dialog_data[selected_course]}:"),
    ScrollingGroup(
        Select(
            Format("🆔 {item[id]} | {item[name]} - 💰 {item[price]} грн"),
            items="products",
            id="product_select",
            item_id_getter=lambda item: str(item["id"]),
            on_click=lambda c, w, m, item_id: c.answer(f"ℹ️ Ви вибрали товар {item_id}")
        ),
        width=1,
        height=10,
        id="products_scroller",
        hide_on_single_page=True
    ),
    ScrollingGroup(
        Select(
            Row(
                Button(Const("➖"), id=Format("decrease_{item[id]}"), on_click=lambda c, w, m, item_id: change_quantity(c, w, m, "decrease", item_id)),
                Format("{dialog_data[products].get(item[id], 0)}"),
                Button(Const("➕"), id=Format("increase_{item[id]}"), on_click=lambda c, w, m, item_id: change_quantity(c, w, m, "increase", item_id)),
            ),
            items="products",
            id="quantity_control",
            item_id_getter=lambda item: str(item["id"])
        ),
        width=1,
        height=10,
        id="quantity_scroller",
        hide_on_single_page=True
    ),
    Row(
        Button(Const("🔙 Назад"), id="back_to_courses", on_click=lambda c, w, m: m.back()),
    ),
    state=OrderSG.show_products,
    getter=get_products
)
