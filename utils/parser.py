# utils/parser.py
from utils.sound import play_error_sound
import re

def parse_trade_data(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    data = {
        "item_id": None,
        "item_name": "",
        "unit_price": 0,
        "quantity": 0,
        "total_price": 0,
        "outlet_type": None,
        "seller_name": ""
    }

    try:
        # Поиск типа лавки
        for line in lines:
            line_lower = line.lower()

            if "buy items" in line_lower and data["outlet_type"] is None:
                parts = line.split(" ", 2)
                data["seller_name"] = parts[2].strip() if len(parts) > 2 else parts[1].strip()
                data["outlet_type"] = 0  # Покупка
                break

            elif "items to sell" in line_lower and data["outlet_type"] is None:
                parts = line.split(" ", 3)
                data["seller_name"] = parts[3].strip() if len(parts) > 3 else parts[2].strip()
                data["outlet_type"] = 1  # Продажа
                break

        if data["outlet_type"] is None:
            data["outlet_type"] = 0
            data["seller_name"] = "Unknown"

        # Unit Price
        for line in lines:
            if "unit price" in line.lower():
                raw = line.split(":", 1)[1].strip()
                digits = ''.join(filter(str.isdigit, raw.split()[0]))
                if digits:
                    data["unit_price"] = float(digits)
                break

        # Quantity
        for line in lines:
            if "quantity" in line.lower():
                raw = line.split(":", 1)[1].strip()
                digits = ''.join(filter(str.isdigit, raw.split()[0]))
                if digits:
                    data["quantity"] = int(digits)
                break

        # 🔍 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Ищем ID ТОЛЬКО в строках с "ID"
        id_pattern = r'(?i)\b(?:id|item\s*id)[\s:]+([0-9,.\s]+)'
        for line in lines:
            match = re.search(id_pattern, line)
            if match:
                # Извлекаем только цифры из найденной части
                id_text = match.group(1)
                clean_id = ''.join(filter(str.isdigit, id_text))
                if clean_id.isdigit() and len(clean_id) >= 3:
                    data["item_id"] = int(clean_id)
                    break  # Нашли ID — выходим

        # 🔁 Резерв: если не нашли через "ID", ищем любое 3–5-значное число
        if not data["item_id"]:
            for line in lines:
                potential = ''.join(filter(str.isdigit, line))
                if potential.isdigit() and 3 <= len(potential) <= 5:
                    # Исключаем типичные ложные срабатывания
                    if int(potential) > 100:  # Не 01, 02, 99
                        data["item_id"] = int(potential)
                        break

        data["total_price"] = data["unit_price"] * data["quantity"]

        print(f"🔍 Найден item_id: {data['item_id']}")
        print(f"📝 Имя предмета: {data['item_name']}")
        print(f"💰 Цена за единицу: {data['unit_price']}")
        print(f"📦 Количество: {data['quantity']}")
        print(f"🧮 Общая сумма: {data['total_price']}")
        print(f"🛒 Тип лавки: {'Покупка' if data['outlet_type'] == 0 else 'Продажа'}")
        print(f"👤 Продавец: {data['seller_name']}")

    except Exception as e:
        print(f"❌ Ошибка при парсинге данных: {e}")

    return data