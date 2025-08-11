# main.py
import tkinter as tk
from utils.tooltip_analyzer import start_tooltip_analyzer
from utils.splash import SplashScreen
from utils.logger import setup_logger
from utils.sound import play_error_sound, play_callout
from core.handler import *
import keyboard
import pygame  # Для звука
import time

# Глобальные переменные
root = None
exit_requested = False

def on_exit():
    """Запрос на выход из приложения"""
    global exit_requested
    print("🛑 Приложение закрыто")
    play_error_sound()
    time.sleep(1)
    exit_requested = True  # Только флаг!

def check_exit():
    """Проверяет, запрошен ли выход, и корректно завершает приложение"""
    global exit_requested
    if exit_requested:
        try:
            root.quit()        # Останавливает mainloop
            root.destroy()     # Уничтожает окно (в основном потоке)
        except tk.TclError:
            pass
        return
    # Повторная проверка через 100 мс
    root.after(100, check_exit)



def get_active_window_process_name():
    """Возвращает имя процесса активного окна"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().lower()
    except:
        return None


def main():
    global root
    setup_logger()

    root = tk.Tk()
    root.withdraw()

    # Показываем splash screen
    splash = SplashScreen()
    root.wait_window(splash.root)

    # Звук уведомления
    play_callout()

    # Запуск анализатора
    start_tooltip_analyzer(root)

    # Горячие клавиши
    keyboard.add_hotkey("ctrl+q", on_exit)
    keyboard.add_hotkey("ctrl+p", restart_program)

    print("🟢 Приложение запущено. Нажмите Left Alt для анализа.")
    print("ℹ️  Для выхода нажмите Ctrl+Q")

    # Запускаем проверку выхода
    root.after(100, check_exit)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_exit()

if __name__ == "__main__":
    main()