# core/handler.py

import keyboard
from utils.screenshot import take_screenshot
from utils.ocr import extract_text_from_image
from utils.parser import parse_trade_data
from database.db import connect_db
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

def start_hotkey_listener():
    keyboard.add_hotkey("ctrl+p", restart_program)


def restart_program():
    """Перезапускает программу при нажатии Ctrl+P."""
    play_loud_sound()
    print("Горячая клавиша Ctrl+P нажата! Перезапуск программы...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

    
def show_all_items(e=None):
    gui.show_all_items_list()