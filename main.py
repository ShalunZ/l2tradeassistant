# main.py
from core.handler import start_hotkey_listener
import tkinter as tk
from tkinter.ttk import Style
from utils.sound import *
from utils.tooltip_analyzer import start_tooltip_analyzer
from utils.logger import setup_logger


setup_logger()
print("Ожидание нажатия Ctrl+E...")
root = tk.Tk()
root.withdraw()
start_hotkey_listener()
play_notification_sound()
start_tooltip_analyzer(root)
root.mainloop()


