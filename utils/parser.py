# utils/parser.py
from utils.sound import play_error_sound
import re
from utils.logger import debug_log



def parse_trade_data(text):
    """
    Парсит текст из OCR.
    Важно:
    - 'Items to Sell' → он продаёт → я могу купить → outlet_type = 0
    - 'Buy Items' → он покупает → я могу продать → outlet_type = 1
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    data = {
        "item_id": None,
        "item_name": "",
        "unit_price": 0,
        "quantity": 0,
        "total_price": 0,
        "outlet_type": 0,  # По умолчанию: "я покупаю"
        "seller_name": "Unknown",
        "calculated_price": False  # Флаг: была ли цена исправлена
    }

    try:
        # --- 1. Определяем тип лавки ---
        for line in lines:
            line_lower = line.lower()
            if "items to sell" in line_lower:
                match = re.search(r'items?\s+to\s+sell[:\-]?\s*([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if match:
                    seller = match.group(1).strip()
                    if seller and len(seller) >= 2:
                        data["seller_name"] = seller
                data["outlet_type"] = 0  # Я покупаю
                break
            elif "buy items" in line_lower:
                match = re.search(r'buy\s+items?[:\-]?\s*([A-Za-z0-9_]+)', line, re.IGNORECASE)
                if match:
                    seller = match.group(1).strip()
                    if seller and len(seller) >= 2:
                        data["seller_name"] = seller
                data["outlet_type"] = 1  # Я продаю
                break

        # --- 2. Unit Price ---
        for line in lines:
            if "unit price" in line.lower():
                clean_line = re.sub(r'unit\s*price\s*[:\-]?', '', line, flags=re.IGNORECASE)
                clean_line = re.sub(r'[^\d,]', '', clean_line)
                numbers = re.findall(r'[\d,]+', clean_line)
                for num_str in numbers:
                    num = int(num_str.replace(',', ''))
                    if num > 0:
                        data["unit_price"] = float(num)
                        break
                break

        # --- 3. Quantity ---
        for line in lines:
            if "quantity" in line.lower():
                clean_line = re.sub(r'quantity\s*[:;\-\|]?\s*', '', line, flags=re.IGNORECASE)
                match = re.search(r'(\d{1,3}(?:,\d{3})*)', clean_line)  # Поддержка 3,125
                if match:
                    qty = int(match.group(1).replace(',', ''))
                    if qty > 0:
                        data["quantity"] = qty
                break

        # --- 4. Total Price ---
        for line in lines:
            if "total price" in line.lower():
                clean_line = re.sub(r'total\s*price\s*[:\-]?', '', line, flags=re.IGNORECASE)
                clean_line = re.sub(r'[^\d,]', '', clean_line)
                numbers = re.findall(r'[\d,]+', clean_line)
                for num_str in numbers:
                    num = int(num_str.replace(',', ''))
                    if num > 0:
                        data["total_price"] = num
                        break
                break

        # --- 5. Item ID ---
        id_pattern = r'\b(?:item\s*id|id)\s*[:\-]?\s*([0-9,.\s]+)'
        for line in lines:
            match = re.search(id_pattern, line, re.IGNORECASE)
            if match:
                id_text = match.group(1)
                clean_id = ''.join(filter(str.isdigit, id_text))
                if clean_id.isdigit() and 3 <= len(clean_id) <= 6:
                    data["item_id"] = int(clean_id)
                    break



        # --- 6. Валидация unit_price через total_price / quantity ---
        if data["quantity"] > 0 and data["total_price"] > 0:
            expected_price = round(data["total_price"] / data["quantity"])
            if abs(data["unit_price"] - expected_price) > 0:  
                print(f"⚠️ OCR дал {data['unit_price']}, но ожидается {expected_price}. Исправляем.")
                data["unit_price"] = float(expected_price)
                data["calculated_price"] = True
            else:
                data["calculated_price"] = False
        else:
            data["calculated_price"] = False

        # --- 7. Обновляем total_price, если unit_price и quantity известны ---
        if data["unit_price"] > 0 and data["quantity"] > 0 and data["total_price"] == 0:
            data["total_price"] = data["unit_price"] * data["quantity"]

        # --- Логирование ---
        print(f"🔍 Найден item_id: {data['item_id']}")
        print(f"📝 Имя предмета: {data['item_name']}")
        print(f"💰 Цена за единицу: {data['unit_price']}")
        print(f"📦 Количество: {data['quantity']}")
        print(f"🧮 Общая сумма: {data['total_price']}")
        print(f"🛒 Тип лавки: {'Покупка' if data['outlet_type'] == 0 else 'Продажа'}")
        print(f"👤 Продавец: {data['seller_name']}")
        print(f"🔧 Исправлена цена: {data['calculated_price']}")

    except Exception as e:
        print(f"❌ Ошибка при парсинге данных: {e}")
        play_error_sound()

    return data