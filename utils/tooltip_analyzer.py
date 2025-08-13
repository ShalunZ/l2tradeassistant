# utils/tooltip_analyzer.py
import keyboard
import time
import threading
import os
import pytesseract
import win32gui
import win32process
import win32api
import win32con
import tkinter as tk

from pynput import mouse
from PIL import ImageGrab
from database.db import connect_db
from utils.parser import parse_trade_data
from io import BytesIO
from config import TESSERACT_PATH
from datetime import datetime
from utils.screenshot import *
from utils.logger import debug_log


pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Настройки

OCR_TIMEOUT = 0.1
TOOLTIP_OFFSET_X = -225  # Отступ от курсора
TOOLTIP_OFFSET_Y = 40

# Папка для отладки
DEBUG_DIR = "debug_screenshots"
os.makedirs(DEBUG_DIR, exist_ok=True)

# Глобальные переменные (в начале файла)
is_alt_pressed = False
current_tooltip = None
last_item_id = None
last_cursor_pos = (0, 0)        # Последняя позиция курсора при анализе
last_check_pos = (0, 0)         # Позиция, с которой начался текущий "стабильный" анализ
item_cache = {}
last_cleanup = time.time()
STABLE_RADIUS = 15               # Пиксели: если в пределах — не перезапускаем OCR



def get_active_window_process_name():
    """Возвращает имя процесса активного окна (без psutil)"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Открываем процесс
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        if not handle:
            return None
            
        # Получаем имя исполняемого файла
        try:
            # Этот вызов может не работать в некоторых контекстах
            exe_name = win32process.GetModuleFileNameEx(handle, 0)
            return exe_name.lower().split('\\')[-1]
        except:
            # Альтернатива: через EnumProcesses (если выше не сработало)
            return str(pid)  # В крайнем случае — хотя бы PID
        finally:
            win32api.CloseHandle(handle)
    except Exception as e:
        return None

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


        img = take_screenshot()
        return img, (x, y)

    except Exception as e:
        debug_log(f"❌ Ошибка при захвате скриншота: {e}")
        return None, (0, 0)


def tooltip_worker(root):
    """Рабочий поток: отслеживает F + мышь"""
    global is_alt_pressed, last_item_id, last_cursor_pos, last_check_pos

    # Для отслеживания остановки мыши
    prev_pos = (0, 0)
    stable_start_time = None
    STABLE_DURATION = 0.2
    MAX_MOVEMENT = 5
    STABLE_RADIUS = 15

    failed_attempts = 0
    MAX_FAILED_ATTEMPTS = 2
    waiting_for_movement = False  # 🔥 Новый флаг

    while True:
        try:
            active_process = get_active_window_process_name()
            in_game = active_process in ['lineageii.exe', 'l2.exe', 'lu4.bin']
            alt_pressed = keyboard.is_pressed('f')

            if alt_pressed and in_game:
                if not is_alt_pressed:
                    is_alt_pressed = True
                    debug_log("✅ F зажат — начинаем анализ (в игре)")

                x, y = mouse.Controller().position
                current_pos = (x, y)
                last_cursor_pos = current_pos

                # --- 1. Проверка: в пределах стабильной зоны? ---
                if last_item_id is not None and last_check_pos != (0, 0):
                    dx = x - last_check_pos[0]
                    dy = y - last_check_pos[1]
                    distance = (dx**2 + dy**2) ** 0.5
                    if distance <= STABLE_RADIUS:
                        # В зоне → не делаем OCR
                        time.sleep(OCR_TIMEOUT)
                        continue

                # --- 2. Проверка: ждём движения после неудач?
                if waiting_for_movement:
                    dx_move = x - prev_pos[0]
                    dy_move = y - prev_pos[1]
                    movement = (dx_move**2 + dy_move**2) ** 0.5
                    if movement > MAX_MOVEMENT:
                        debug_log("🟢 Мышь сдвинулась — сбрасываем счётчик неудач")
                        failed_attempts = 0
                        waiting_for_movement = False
                        stable_start_time = None  # Сброс таймера остановки
                    time.sleep(OCR_TIMEOUT)
                    continue

                # --- 3. Проверка: мышь остановилась? ---
                dx_move = x - prev_pos[0]
                dy_move = y - prev_pos[1]
                movement = (dx_move**2 + dy_move**2) ** 0.5
                prev_pos = current_pos

                if movement <= MAX_MOVEMENT:
                    if stable_start_time is None:
                        stable_start_time = time.time()
                    elif time.time() - stable_start_time >= STABLE_DURATION:
                        pass  # Можно анализировать
                    else:
                        time.sleep(OCR_TIMEOUT)
                        continue
                else:
                    stable_start_time = None
                    time.sleep(OCR_TIMEOUT)
                    continue

                # --- Делаем скриншот и OCR ---
                img, pos = get_cursor_area()
                if img is None:
                    time.sleep(OCR_TIMEOUT)
                    continue

                data = parse_trade_data(pytesseract.image_to_string(img, lang='eng', config='--psm 6'))
                item_id = data["item_id"]
                debug_log(f"🔍 OCR нашёл item_id: {item_id}")

                if item_id:
                    failed_attempts = 0  # ✅ Успех — сбрасываем

                    info = get_item_info(item_id)
                    if info and info["name"] == "Нет данных":
                        debug_log("🟡 Нет данных в БД — принудительный повтор OCR")
                        time.sleep(OCR_TIMEOUT)
                        continue

                    if info:
                        show_tooltip(info, pos)
                        last_item_id = item_id
                        last_check_pos = pos
                    else:
                        debug_log("❌ Не удалось получить данные для тултипа")
                else:
                    failed_attempts += 1
                    debug_log(f"🟡 Неудачная попытка OCR #{failed_attempts} (без item_id)")

                    if failed_attempts >= MAX_FAILED_ATTEMPTS:
                        debug_log("🔴 Достигнуто максимальное количество неудачных попыток. Ждём движения мыши...")
                        waiting_for_movement = True  # 🔥 Включаем ожидание
                        failed_attempts = 0  # Сбрасываем для будущих попыток
                        stable_start_time = None  # Сбрасываем таймер остановки
                        # → следующие итерации будут только проверять движение
                    else:
                        time.sleep(OCR_TIMEOUT)
                        continue

            elif is_alt_pressed:
                is_alt_pressed = False
                debug_log("🔴 F отжат — останавливаем анализ")
                hide_tooltip()
                last_item_id = None
                last_check_pos = (0, 0)
                stable_start_time = None
                failed_attempts = 0
                waiting_for_movement = False

            time.sleep(OCR_TIMEOUT)

        except Exception as e:
            debug_log(f"💀 Критическая ошибка в tooltip_worker: {e}")
            time.sleep(1)

def start_tooltip_analyzer(root):
    """Запускает анализатор подсказок"""
    thread = threading.Thread(target=tooltip_worker, args=(root,), daemon=True)
    thread.start()
    debug_log("🚀 Tooltip Analyzer запущен. Нажмите F + наведите на предмет.")