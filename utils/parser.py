# utils/parser.py
from utils.sound import play_error_sound
import re

def parse_trade_data(text):
    """
    Парсит текст из OCR.
    Важно: 
    - 'Items to Sell' → продавец продаёт → я могу купить → outlet_type = 0
    - 'Buy Items' → продавец покупает → я могу продать → outlet_type = 1
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    data = {
        "item_id": None,
        "item_name": "",
        "unit_price": 0,
        "quantity": 0,
        "total_price": 0,
        "outlet_type": 0,  # По умолчанию: "я покупаю" (он продаёт)
        "seller_name": "Unknown"
    }

    try:
        # --- 1. Определяем тип лавки ---
        for line in lines:
            line_lower = line.lower()
            # "Items to Sell" → он продаёт → я покупаю → outlet_type = 0
            if "items to sell" in line_lower:
                parts = line.split(" ", 3)
                seller = parts[3].strip() if len(parts) > 3 else parts[2].strip()
                if seller and not seller.isdigit():
                    data["seller_name"] = seller
                data["outlet_type"] = 0  # Я покупаю
                break
            # "Buy Items" → он покупает → я продаю → outlet_type = 1
            elif "buy items" in line_lower:
                parts = line.split(" ", 2)
                seller = parts[2].strip() if len(parts) > 2 else parts[1].strip()
                if seller and not seller.isdigit():
                    data["seller_name"] = seller
                data["outlet_type"] = 1  # Я продаю
                break

        # --- 2. Unit Price ---
        total_price = 0
        for line in lines:
            if "unit price" in line.lower():
                clean_line = re.sub(r'unit\s*price\s*[:\-]?', '', line, flags=re.IGNORECASE)
                clean_line = re.sub(r'[^\d,]', '', clean_line)
                numbers = re.findall(r'[\d,]+', clean_line)
                for num_str in numbers:
                    num = int(num_str.replace(',', ''))
                    if num > 0:  # Разумная цена
                        data["unit_price"] = float(num)
                        break
                break

        # --- 3. Quantity ---
        for line in lines:
            line_lower = line.lower()
            if "quantity" in line_lower:
                # Убираем "quantity", двоеточия, точки, артефакты
                clean_line = re.sub(r'quantity\s*[:;\-\|]?\s*', '', line, flags=re.IGNORECASE)
                # Извлекаем первое число
                match = re.search(r'(\d+)', clean_line)
                if match:
                    qty = int(match.group(1))
                    if qty > 0:
                        data["quantity"] = qty
                break

        # --- 4. Item ID ---
        id_pattern = r'\b(?:item\s*id|id)\s*[:\-]?\s*([0-9,.\s]+)'
        for line in lines:
            match = re.search(id_pattern, line, re.IGNORECASE)
            if match:
                id_text = match.group(1)
                clean_id = ''.join(filter(str.isdigit, id_text))
                if clean_id.isdigit() and 3 <= len(clean_id) <= 6:
                    data["item_id"] = int(clean_id)
                    break

        # Резерв: любое 3–6-значное число
        if not data["item_id"]:
            for line in lines:
                nums = re.findall(r'\b\d{3,6}\b', line.replace(',', ''))
                for num_str in nums:
                    num = int(num_str)
                    if num > 100 and num != data["unit_price"] and num != data["quantity"]:
                        data["item_id"] = num
                        break
                if data["item_id"]:
                    break

        # --- 5. Total Price ---
        data["total_price"] = data["unit_price"] * data["quantity"]

        # --- Логирование ---
        print(f"🔍 Найден item_id: {data['item_id']}")
        print(f"📝 Имя предмета: {data['item_name']}")
        print(f"💰 Цена за единицу: {data['unit_price']}")
        print(f"📦 Количество: {data['quantity']}")
        print(f"🧮 Общая сумма: {data['total_price']}")
        print(f"🛒 Тип лавки: {'Покупка' if data['outlet_type'] == 0 else 'Продажа'}")
        print(f"👤 Продавец: {data['seller_name']}")

    except Exception as e:
        print(f"❌ Ошибка при парсинге данных: {e}")
        play_error_sound()

    return data