# main.py
from core.handler import start_hotkey_listener
import tkinter as tk
from tkinter.ttk import Style
from utils.sound import play_error_sound, play_success_sound,play_notification_sound
from utils.tooltip_analyzer import start_tooltip_analyzer



print("Ожидание нажатия Ctrl+E...")
root = tk.Tk()
root.withdraw()
start_hotkey_listener()
play_notification_sound()
start_tooltip_analyzer(root)
root.mainloop()


def test_tooltip():
    from tooltip_analyzer import show_tooltip
    show_tooltip({
        "item_id": 999,
        "name": "Тестовый предмет",
        "best_buy": 100,
        "best_sell": 200,
        "med_buy": 110,
        "med_sell": 190
    }, (100, 100))

# Где-то в GUI
tk.Button(root, text="Тест тултип", command=test_tooltip).pack()