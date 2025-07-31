# utils/parser.py
from utils.sound import play_error_sound

def parse_trade_data(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    data = {
        "item_id": None,
        "item_name": "",
        "unit_price": 0,
        "quantity": 0,
        "total_price": 0,
        "outlet_type": None,        # 0 = Продажа, 1 = Покупка
        "seller_name": ""           # Имя игрока из строки "Buy Items ..." или "Items to Sell ..."
    }

    try:
        # Поиск строк с типом лавки
        for line in lines:
            line_lower = line.lower()

            # Случай: "Buy Items <имя>"
            if "buy items" in line_lower and not data["outlet_type"]:
                parts = line.split(" ", 2)  # Разбиваем по словам
                if len(parts) > 2:
                    data["seller_name"] = parts[2].strip()
                elif len(parts) == 2:
                    data["seller_name"] = parts[1].strip()
                data["outlet_type"] = 0  # Покупка
                break

            # Случай: "Items to Sell <имя>"
            elif "items to sell" in line_lower and not data["outlet_type"]:
                parts = line.split(" ", 3)  # "Items to Sell Saxarock"
                if len(parts) > 3:
                    data["seller_name"] = parts[3].strip()
                elif len(parts) == 3:
                    data["seller_name"] = parts[2].strip()
                data["outlet_type"] = 1  # Продажа
                break

        # Если не удалось определить тип лавки
        if data["outlet_type"] is None:
            print("⚠️ Не удалось определить тип лавки (Buy Items / Items to Sell)")
            data["outlet_type"] = 0  # Дефолт: продажа
            data["seller_name"] = "Unknown"

        # Парсим Unit Price
        unit_price_idx = None
        for i, line in enumerate(lines):
            if "unit price" in line.lower():
                unit_price_idx = i
                break

        if unit_price_idx is not None:
            raw_unit_price = lines[unit_price_idx].split(":")[1].strip()
            clean_unit_price = ''.join(filter(str.isdigit, raw_unit_price.split()[0]))
            if clean_unit_price:
                data["unit_price"] = float(clean_unit_price)

        # Парсим Quantity
        quantity_idx = None
        for i, line in enumerate(lines):
            if "quantity" in line.lower():
                quantity_idx = i
                break

        if quantity_idx is not None:
            raw_quantity = lines[quantity_idx].split(":")[1].strip()
            clean_quantity = ''.join(filter(str.isdigit, raw_quantity.split()[0]))
            if clean_quantity:
                data["quantity"] = int(clean_quantity)

        # Парсим Item ID
        for line in lines:
            if "id" in line.lower() and ":" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    raw_id = parts[1].strip()
                    clean_id = ''.join(filter(str.isdigit, raw_id))
                    if clean_id:
                        data["item_id"] = int(clean_id)
                        break

        # Если ID не найден — ищем любое число длиной 3–5 цифр
        if not data["item_id"]:
            for line in lines:
                potential_id = ''.join(filter(str.isdigit, line))
                if potential_id.isdigit() and 3 <= len(potential_id) <= 5:
                    data["item_id"] = int(potential_id)
                    break

        # Вычисляем общую сумму
        data["total_price"] = data["unit_price"] * data["quantity"]

        # Логируем результат
        print(f"🔍 Найден item_id: {data['item_id']}")
        print(f"📝 Имя предмета: {data['item_name']}")
        print(f"💰 Цена за единицу: {data['unit_price']}")
        print(f"📦 Количество: {data['quantity']}")
        print(f"🧮 Общая сумма: {data['total_price']}")
        print(f"🛒 Тип лавки: {'Покупка' if data['outlet_type'] == 1 else 'Продажа'}")
        print(f"👤 Продавец: {data['seller_name']}")

    except Exception as e:
        print(f"❌ Ошибка при парсинге данных: {e}")
        play_error_sound()

    return data