# main.py
import tkinter as tk
from utils.tooltip_analyzer import start_tooltip_analyzer
from utils.splash import SplashScreen
from utils.logger import setup_logger
from utils.sound import play_error_sound, play_callout
from core.handler import restart_program
from utils.tray import *
import keyboard
import pygame
import time
import threading

# Глобальные переменные
root = None
exit_requested = False
tray_icon = None

def on_exit():
    """Запрос на выход из приложения"""
    global exit_requested, tray_icon
    print("🛑 Приложение закрыто")
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
    setup_logger()

    root = tk.Tk()
    root.withdraw()

    # Показываем splash screen
    splash = SplashScreen()
    root.wait_window(splash.root)
    
    #Проверяем обновления 
    from updater import check_and_update
    if check_and_update():
        return

    # Звук уведомления
    play_callout()

    # Запуск анализатора
    start_tooltip_analyzer(root)

    # Горячие клавиши
    keyboard.add_hotkey("ctrl+q", on_exit)
    keyboard.add_hotkey("ctrl+p", restart_program)

    print("🟢 Приложение запущено. Нажмите F для анализа.")
    print("ℹ️  Для выхода нажмите Ctrl+Q")

    # Запускаем проверку выхода
    root.after(100, check_exit)

    # Запускаем трей в отдельном потоке
    tray_thread = threading.Thread(target=start_tray, daemon=True)
    tray_thread.start()


    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_exit()

if __name__ == "__main__":
    main()