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
        cur.execute("""
            SELECT 
                item_name,
                best_buy_price,
                best_sell_price,
                median_buy_price,
                median_sell_price
            FROM vw_trade_deals 
            WHERE item_id = %s
        """, (item_id,))
        row = cur.fetchone()
        conn.close()

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

        item_cache[item_id] = {"data": info, "timestamp": time.time()}
        return info

    except Exception as e:
        debug_log(f"❌ Ошибка при запросе к БД: {e}")
        return {
            "item_id": item_id,
            "name": "Ошибка",
            "best_buy": "?", "best_sell": "?", "med_buy": "?", "med_sell": "?"
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

    if current_tooltip:
        hide_tooltip()

    try:
        # Создаём Toplevel как дочерний от основного root
        dialog = tk.Toplevel(tk._default_root)
        dialog.overrideredirect(True)  # Убираем рамку
        dialog.attributes("-topmost", True)  # Поверх всех
        dialog.attributes("-alpha", 0.95)  # Прозрачность

        # 🔥 КЛЮЧЕВОЕ: делаем окно "прозрачным" для мыши
        dialog.wm_attributes("-transparentcolor", "#1e1e1e")  # Цвет, который станет прозрачным
        bg_color = "#1e1e1e"  # Этот цвет исчезнет
        dialog.configure(bg=bg_color)

        # Формируем текст
        profit_line = ""
        if isinstance(info['best_buy'], int) and isinstance(info['best_sell'], int):
            profit = info['best_sell'] - info['best_buy']
            profit_line = f"\n💰 Профит: {profit}"

        text = (
            f"ID: {info['item_id']}\n"
            f"{info['name']}\n\n"
            f"🟢 Покупка: {info['best_buy']}\n"
            f"🔴 Продажа: {info['best_sell']}{profit_line}\n"
            f"📊 Медиана: {info['med_buy']} / {info['med_sell']}"
        )

        label = tk.Label(
            dialog,
            text=text,
            justify="left",
            font=("Consolas", 9, "bold"),
            bg="#2a2a2a",  # Цвет фона лейбла (не совпадает с transparentcolor!)
            fg="#e0e0e0",
            anchor="w",
            padx=12,
            pady=10
        )
        label.pack()

        # Позиционирование: справа от курсора
        x, y = cursor_pos
        dialog.update_idletasks()
        w, h = dialog.winfo_width(), dialog.winfo_height()

        # Размещаем окно
        dialog.geometry(f"{w}x{h}+{x + TOOLTIP_OFFSET_X}+{y - TOOLTIP_OFFSET_Y}")

        # 🔁 Обновляем позицию в реальном времени
        def follow_mouse():
            nonlocal dialog, label
            while dialog.winfo_exists() and current_tooltip == dialog:
                try:
                    x, y = mouse.Controller().position
                    dialog.geometry(f"{w}x{h}+{x + TOOLTIP_OFFSET_X}+{y - TOOLTIP_OFFSET_Y}")
                    time.sleep(0.05)  # Обновление 20 раз в секунду
                except tk.TclError:
                    break  # Окно закрыто

            debug_log("🔴 Следование за мышью остановлено")

        # Запускаем в отдельном потоке
        follow_thread = threading.Thread(target=follow_mouse, daemon=True)
        follow_thread.start()

        current_tooltip = dialog
        debug_log(f"🟢 Показан тултип для item_id: {info['item_id']}")

    except Exception as e:
        debug_log(f"❌ Ошибка при создании тултипа: {e}")


def hide_tooltip():
    """Скрывает текущее всплывающее окно"""
    global current_tooltip
    if current_tooltip:
        try:
            current_tooltip.destroy()
            debug_log("🔴 Тултип скрыт")
        except Exception as e:
            debug_log(f"❌ Ошибка при скрытии тултипа: {e}")
        current_tooltip = None


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
            alt_pressed = keyboard.is_pressed('alt')

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
                    last_item_id = None

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