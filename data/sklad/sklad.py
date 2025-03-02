def show_all_stock(bot, message):
    """Генерує PDF-файл зі списком товарів і надсилає користувачу."""
    # Надсилаємо повідомлення про очікування
    wait_message = bot.send_message(message.chat.id, "⏳ Зачекайте, документ формується...")

    items = get_all_stock()

    # Отримуємо поточний час у Києві
    now = datetime.now(kyiv_tz).strftime("%Y-%m-%d_%H-%M")

    # Формуємо назву файлу
    filename = f"sklad_HD_{now}.pdf"

    # Створюємо PDF-документ
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Використовуємо стандартний шрифт
    pdf.set_font("Helvetica", style="B", size=16)

    # Заголовок (без емодзі)
    pdf.cell(200, 10, f"Наявність товарів на складі (станом на {now})", ln=True, align="C")
    pdf.ln(10)

    # Створюємо таблицю
    pdf.set_font("Helvetica", size=10)
    pdf.cell(20, 8, "ID", border=1, align="C")
    pdf.cell(50, 8, "Курс", border=1, align="C")
    pdf.cell(50, 8, "Товар", border=1, align="C")
    pdf.cell(20, 8, "На складі", border=1, align="C")
    pdf.cell(20, 8, "Доступно", border=1, align="C")
    pdf.cell(20, 8, "Ціна", border=1, align="C")
    pdf.ln()

    # Додаємо дані в таблицю
    for item in items:
        pdf.cell(20, 8, str(item["id"]), border=1, align="C")
        pdf.cell(50, 8, item["course"], border=1, align="L")
        pdf.cell(50, 8, item["name"], border=1, align="L")
        pdf.cell(20, 8, str(item["stock"]), border=1, align="C")
        pdf.cell(20, 8, str(item["available"]), border=1, align="C")
        pdf.cell(20, 8, f"{item['price']}₴", border=1, align="C")
        pdf.ln()

    # Зберігаємо PDF
    pdf.output(filename, "F")

    # Видаляємо повідомлення "Зачекайте..."
    bot.delete_message(chat_id=message.chat.id, message_id=wait_message.message_id)

    # Відправляємо файл користувачу
    with open(filename, "rb") as file:
        bot.send_document(message.chat.id, file, caption="📄 Ось список наявних товарів на складі.")

    # Видаляємо тимчасовий файл
    os.remove(filename)
