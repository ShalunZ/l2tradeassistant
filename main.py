# main.py
import tkinter as tk
import keyboard
import pygame
import time
import threading


from utils.tooltip_analyzer import start_tooltip_analyzer
from utils.splash import SplashScreen
from utils.sound import play_error_sound, play_callout
from utils.logger import close_logger,debug_log

from core.handler import restart_program
from utils.tray import *
from updater import check_and_update





# Глобальные переменные
root = None
exit_requested = False
tray_icon = None

def on_exit():
    """Запрос на выход из приложения"""
    global exit_requested, tray_icon
    debug_log("🛑 Приложение закрыто")
    play_error_sound()
    time.sleep(0.7)
    exit_requested = True
    if tray_icon:
        tray_icon.stop()  # Остановить иконку в трее

def check_exit():
    """Проверяет, запрошен ли выход, и корректно завершает приложение"""
    global exit_requested
    if exit_requested:
        try:
            close_logger()
            root.quit()
            root.destroy()
        except tk.TclError:
            pass
        return
    root.after(100, check_exit)

def start_tray():
    """Запускает иконку в трее в отдельном потоке"""
    global tray_icon
    tray_icon = create_tray_icon(on_exit)

def main():
    global root

    root = tk.Tk()
    root.withdraw()

    # Показываем splash screen
    splash = SplashScreen()
    root.wait_window(splash.root)
    
    from updater import check_and_update
    if check_and_update():
        play_success_sound()




    # Запуск анализатора
    start_tooltip_analyzer(root)

    # Горячие клавиши
    keyboard.add_hotkey("ctrl+q", on_exit)
    keyboard.add_hotkey("ctrl+p", restart_program)

    debug_log("🟢 Приложение запущено. Нажмите F для анализа.")
    debug_log("ℹ️  Для выхода нажмите Ctrl+Q")

    # Запускаем проверку выхода
    root.after(100, check_exit)

    # Запускаем трей в отдельном потоке
    tray_thread = threading.Thread(target=start_tray, daemon=True)
    tray_thread.start()

     # Звук уведомления
    play_callout()
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_exit()

if __name__ == "__main__":
    main()