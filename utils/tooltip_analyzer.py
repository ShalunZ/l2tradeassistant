# utils/tooltip_analyzer.py
import keyboard
import time
import threading
from pynput import mouse
from PIL import ImageGrab
import tkinter as tk
from database.db import connect_db
from utils.parser import parse_trade_data
from io import BytesIO
import os
from datetime import datetime
import pytesseract
from config import TESSERACT_PATH
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Настройки
AREA_SIZE = 500
OCR_TIMEOUT = 0.05
TOOLTIP_OFFSET_X = -225  # Отступ от курсора
TOOLTIP_OFFSET_Y = 40

# Папка для отладки
DEBUG_DIR = "debug_screenshots"
os.makedirs(DEBUG_DIR, exist_ok=True)

# Глобальные переменные
is_alt_pressed = False
current_tooltip = None
last_item_id = None
item_cache = {}
last_cleanup = time.time()

# 🔧 Включить/выключить дебаг
DEBUG = True


def debug_log(message):
    if DEBUG:
        print(f"[Tooltip Analyzer] {message}")


def cleanup_cache():
    global item_cache, last_cleanup
    now = time.time()
    if now - last_cleanup > 60:
        item_cache = {k: v for k, v in item_cache.items() if (now - v['timestamp']) < 300}
        debug_log(f"🧹 Кэш очищен: {len(item_cache)} записей")
        last_cleanup = now


def get_item_info(item_id):
    debug_log(f"🔍 Запрос данных для item_id: {item_id}")
    cleanup_cache()

    if item_id in item_cache:
        debug_log(f"✅ Найдено в кэше: {item_id}")
        return item_cache[item_id]['data']

    try:
        conn = connect_db()
        if not conn:
            debug_log("❌ Не удалось подключиться к БД")
            return None

        cur = conn.cursor()

        # 1. Получаем данные о рынке
        cur.execute("""
            SELECT 
                item_name,
                best_buy_price,
                best_sell_price,
                median_buy_price,
                median_sell_price
            FROM vw_trade_deals 
            WHERE item_id = ?
        """, (item_id,))
        row = cur.fetchone()

        # 2. Получаем данные о крафте
        cur.execute("""
            SELECT 
                current_buy_price, 
                crafting_cost, 
                profit_from_craft, 
                profit_percent, 
                recommendation
            FROM vw_craft_profit 
            WHERE item_id = ?
        """, (item_id,))
        craft_row = cur.fetchone()

        conn.close()

        # Формируем базовую информацию
        if row:
            name, buy, sell, med_buy, med_sell = row
            info = {
                "item_id": item_id,
                "name": name or "Неизвестно",
                "best_buy": int(buy) if buy else "-",
                "best_sell": int(sell) if sell else "-",
                "med_buy": int(med_buy) if med_buy else "-",
                "med_sell": int(med_sell) if med_sell else "-"
            }
            debug_log(f"✅ Данные из БД: {info}")
        else:
            debug_log(f"🟡 Нет данных в БД для item_id {item_id}")
            info = {
                "item_id": item_id,
                "name": "Нет данных",
                "best_buy": "-", "best_sell": "-", "med_buy": "-", "med_sell": "-"
            }

        # Добавляем информацию о крафте
        if craft_row:
            buy_price, cost, profit, percent, rec = craft_row
            info["craft_info"] = {
                "buy_price": int(buy_price) if buy_price else 0,
                "cost": int(cost) if cost else 0,
                "profit": int(profit) if profit else 0,
                "percent": float(percent) if percent else 0.0,
                "rec": rec or "⚪ Нет данных"
            }
            debug_log(f"🔧 Информация о крафте: {info['craft_info']}")
        else:
            info["craft_info"] = {
                "buy_price": 0,
                "cost": 0,
                "profit": 0,
                "percent": 0.0,
                "rec": "⚪ Нет данных"
            }

        # Сохраняем в кэш
        item_cache[item_id] = {"data": info, "timestamp": time.time()}

        return info

    except Exception as e:
        debug_log(f"❌ Ошибка при запросе к БД: {e}")
        return {
            "item_id": item_id,
            "name": "Ошибка",
            "best_buy": "?", "best_sell": "?", "med_buy": "?", "med_sell": "?",
            "craft_info": {
                "buy_price": 0, "cost": 0, "profit": 0, "percent": 0.0, "rec": "🔴 Ошибка"
            }
        }


def get_tooltip_color(info):
    try:
        buy = info['best_buy']
        sell = info['best_sell']
        if isinstance(buy, int) and isinstance(sell, int) and sell > buy * 1.2:
            return "#006400"
        elif isinstance(sell, int) and isinstance(buy, int) and sell > buy:
            return "#228B22"
        else:
            return "#8B0000"
    except:
        return "#1e1e1e"

def show_tooltip(info, cursor_pos):
    """Показывает всплывающее окно рядом с курсором — невидимое и неинтерактивное"""
    global current_tooltip

    try:
        # 🌟 1. Создаём или переиспользуем Toplevel
        if current_tooltip is None:
            # Создаём один раз
            dialog = tk.Toplevel(tk._default_root)
            dialog.withdraw()  # Скрываем сразу
            dialog.overrideredirect(True)
            dialog.attributes("-topmost", True)
            dialog.attributes("-alpha", 0)  # Полная прозрачность
            dialog.wm_attributes("-transparentcolor", "#1e1e1e")  # Прозрачный цвет
            dialog.configure(bg="#1e1e1e")

            # Создаём Label и держим ссылку
            label = tk.Label(
                dialog,
                justify="left",
                font=("Consolas", 9, "bold"),
                fg="#e0e0e0",
                anchor="w",
                padx=12,
                pady=10
            )
            label.pack()

            # Сохраняем как current_tooltip
            current_tooltip = {
                "window": dialog,
                "label": label,
                "follow_thread": None,
                "is_visible": False
            }
        else:
            dialog = current_tooltip["window"]
            label = current_tooltip["label"]

        # 🌟 2. Обновляем текст и стиль
        craft_line = ""
        bg_label_color = "#2a2a2a"

        if info.get("craft_info"):
            craft = info["craft_info"]
            cost = int(craft["cost"])
            rec = craft["rec"]

            if rec == "🟢 Купи готовый":
                craft_line = f"\n🧱 Себестоимость: {cost:,}\n🔧 {rec}"
                bg_label_color = "#3a3a2a"
            elif rec == "🟡 Крафти сам":
                profit_craft = int(craft["profit"])
                craft_line = f"\n🧱 Себестоимость: {cost:,}\n💰 Профит: {profit_craft:,}\n🔧 {rec}"
                bg_label_color = "#2a3a2a"
            elif rec == "🔴 Не выгодно":
                craft_line = f"\n🧱 Себестоимость: {cost:,}\n🔧 {rec}"
                bg_label_color = "#3a2a2a"

        text = (
            f"ID: {info['item_id']}\n"
            f"{info['name']}\n\n"
            f"🟢 Buy: {info['best_buy']}\n"
            f"🔴 Sell: {info['best_sell']}\n"
            f"📊 Median: {info['med_buy']} / {info['med_sell']}{craft_line}"
        )

        label.config(text=text, bg=bg_label_color)
        dialog.update_idletasks()  # Получаем актуальные размеры

        # 🌟 3. Позиционируем
        w, h = dialog.winfo_width(), dialog.winfo_height()
        x, y = cursor_pos
        dialog.geometry(f"{w}x{h}+{x + TOOLTIP_OFFSET_X}+{y - TOOLTIP_OFFSET_Y}")

        # 🌟 4. Показываем (если был скрыт)
        if not current_tooltip["is_visible"]:
            dialog.deiconify()  # Показываем
            dialog.attributes("-alpha", 0.95)  # Делаем видимым
            current_tooltip["is_visible"] = True

        # 🌟 5. Перемещаем в реальном времени
        if current_tooltip["follow_thread"] is None or not current_tooltip["follow_thread"].is_alive():
            def follow_mouse():
                while current_tooltip and current_tooltip["is_visible"]:
                    try:
                        x, y = mouse.Controller().position
                        dialog.geometry(f"{w}x{h}+{x + TOOLTIP_OFFSET_X}+{y - TOOLTIP_OFFSET_Y}")
                        time.sleep(0.05)
                    except (tk.TclError, AttributeError):
                        break
                debug_log("🔴 Следование за мышью остановлено")

            thread = threading.Thread(target=follow_mouse, daemon=True)
            current_tooltip["follow_thread"] = thread
            thread.start()

        debug_log(f"🟢 Показан тултип для item_id: {info['item_id']}")

    except Exception as e:
        debug_log(f"❌ Ошибка при создании тултипа: {e}")

def hide_tooltip():
    """Скрывает текущее всплывающее окно без уничтожения"""
    global current_tooltip
    if current_tooltip:
        try:
            # Просто скрываем
            current_tooltip["window"].withdraw()
            current_tooltip["window"].attributes("-alpha", 0)
            current_tooltip["is_visible"] = False
            debug_log("🔴 Тултип скрыт (не уничтожен)")
        except Exception as e:
            debug_log(f"❌ Ошибка при скрытии тултипа: {e}")
        current_tooltip["follow_thread"] = None


def get_cursor_area():
    """Делает скриншот области вокруг курсора"""
    try:
        x, y = mouse.Controller().position
        debug_log(f"🖱️ Позиция курсора: ({x}, {y})")

        left = x 
        top = y 
        right = left + AREA_SIZE
        bottom = top + AREA_SIZE

        img = ImageGrab.grab(bbox=(left, top, right, bottom))
        return img, (x, y)

    except Exception as e:
        debug_log(f"❌ Ошибка при захвате скриншота: {e}")
        return None, (0, 0)


def tooltip_worker(root):
    """Рабочий поток: отслеживает Alt + мышь"""
    global is_alt_pressed, last_item_id

    debug_log("🟢 Tooltip Analyzer запущен. Ожидание Alt...")

    while True:
        try:
            alt_pressed = keyboard.is_pressed('F')

            if alt_pressed:
                if not is_alt_pressed:
                    is_alt_pressed = True
                    debug_log("✅ Alt зажат — начинаем анализ")

                img, pos = get_cursor_area()
                if img is None:
                    time.sleep(OCR_TIMEOUT)
                    continue

                # Используем парсер ТОЛЬКО для item_id
                data = parse_trade_data(pytesseract.image_to_string(img, lang='eng', config='--psm 6'))
                item_id = data["item_id"]

                debug_log(f"🔍 OCR нашёл item_id: {item_id}")

                if item_id and item_id != last_item_id:
                    info = get_item_info(item_id)
                    if info:
                        show_tooltip(info, pos)
                        last_item_id = item_id
                    else:
                        debug_log("❌ Не удалось получить данные для тултипа")
                elif not item_id and current_tooltip:
                    hide_tooltip()


            else:
                if is_alt_pressed:
                    is_alt_pressed = False
                    debug_log("🔴 Alt отжат — останавливаем анализ")
                    hide_tooltip()
                    last_item_id = None

            time.sleep(OCR_TIMEOUT)

        except Exception as e:
            debug_log(f"💀 Критическая ошибка в tooltip_worker: {e}")
            time.sleep(1)


def start_tooltip_analyzer(root):
    """Запускает анализатор подсказок"""
    thread = threading.Thread(target=tooltip_worker, args=(root,), daemon=True)
    thread.start()
    debug_log("🚀 Tooltip Analyzer запущен. Нажмите Left Alt + наведите на предмет.")