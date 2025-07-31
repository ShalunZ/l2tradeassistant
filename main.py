# main.py
from core.handler import start_hotkey_listener
import tkinter as tk
from tkinter.ttk import Style
from utils.sound import play_error_sound, play_success_sound,play_notification_sound


print("Ожидание нажатия Ctrl+E...")
root = tk.Tk()
root.withdraw()
start_hotkey_listener()
play_notification_sound()
root.mainloop()
