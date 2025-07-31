# core/handler.py

import keyboard
from utils.screenshot import take_screenshot
from utils.ocr import extract_text_from_image
from utils.parser import parse_trade_data
from database.db import connect_db, save_to_db, ensure_item_exists
from gui.trade_gui import TradeLoggerGUI
import threading
import tkinter as tk
import sys, os
from utils.sound import *

processing = False
data_for_gui = {}  # Храним данные для Ctrl+F
main_root = None   # Единый экземпляр Tk()
main_gui = None    # Глобальный доступ к GUI

def set_main_app(root, gui):
    global main_root, main_gui
    main_root = root
    main_gui = gui

def on_key_press(e=None):
    global processing, data_for_gui, main_root, main_gui
    if processing:
        return
    processing = True
    print("Горячая клавиша Ctrl+E нажата!")

    img = take_screenshot()
    text = extract_text_from_image(img)
    print("Распознанный текст:")
    print(text)

    data = parse_trade_data(text)
    if data["item_id"]:
        print(f"🔍 Найден item_id: {data['item_id']}")
        print(f"📝 Предположительное имя предмета: {data.get('item_name', 'Не найдено')}")
        print(f"💰 Цена за единицу: {data['unit_price']}")
        print(f"📦 Количество: {data['quantity']}")
        print(f"🧮 Общая сумма: {data['total_price']}")

        data_for_gui = data

        # Открываем диалоговое окно подтверждения
        if not main_root:
            root = tk.Tk()
            root.withdraw()
            gui = TradeLoggerGUI(root)
            set_main_app(root, gui)

        main_gui.show_confirmation_dialog(data)

    else:
        print("❌ Не удалось распознать item_id")
        data_for_gui = {}

    processing = False


def show_deal_info_window(e=None):
    """Обработка нажатия Ctrl+F — показывает статистику по товару"""
    global data_for_gui, main_gui, processing
    if processing:
        return
    if not data_for_gui:
        print("❌ Нет данных для отображения статистики.")
        return

    item_id = data_for_gui.get("item_id")
    if not item_id:
        print("❌ Нет item_id для отображения статистики.")
        return

    print(f"🔍 Запрашиваем информацию по item_id: {item_id}")

    if main_gui:
        main_gui.show_deal_info(data_for_gui)
    else:
        print("❌ GUI не инициализирован.")

def start_hotkey_listener():
    keyboard.add_hotkey("ctrl+e", on_key_press)
    keyboard.add_hotkey("ctrl+f", show_deal_info_window)
    keyboard.add_hotkey("ctrl+p", restart_program)


def restart_program():
    """Перезапускает программу при нажатии Ctrl+P."""
    play_loud_sound()
    print("Горячая клавиша Ctrl+P нажата! Перезапуск программы...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

    
def show_all_items(e=None):
    gui.show_all_items_list()