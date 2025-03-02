def check_user_in_database(self, phone_number):
    """
    Перевіряє, чи є номер телефону у базі Google Sheets.
    Повертає ID, ім'я, email та роль користувача.
    """
    phone_number = self.clean_phone_number(phone_number)

    # Отримуємо всі значення з таблиці
    all_data = self.sheet.get_all_values()

    # Фільтруємо лише ті рядки, де є номер телефону
    valid_rows = [row for row in all_data[1:] if len(row) > 1 and row[1].strip()]

    # Витягуємо тільки чисті номери телефонів
    phone_numbers = [self.clean_phone_number(row[1].strip()) for row in valid_rows]

    print(f"DEBUG: Отримано номер: {phone_number}")
    print(f"DEBUG: Номери в базі (після очищення): {phone_numbers}")

    if phone_number in phone_numbers:
        row_index = phone_numbers.index(phone_number)  # Знаходимо правильний індекс
        found_data = valid_rows[row_index]  # Беремо відповідний рядок

        print(f"DEBUG: Знайдено рядок у таблиці: {found_data}")

        # Отримуємо дані користувача з відповідних стовпців
        user_id = found_data[0].strip() if len(found_data) > 0 else "Невідомий ID"
        user_name = found_data[2].strip() if len(found_data) > 2 else "Невідомий користувач"
        email = found_data[3].strip() if len(found_data) > 3 else "Немає email"
        user_role = found_data[6].strip() if len(found_data) > 6 else "Невідома роль"

        return user_id, user_name, email, user_role  # Повертаємо всі 4 значення

    return None  # Якщо номер не знайдено
