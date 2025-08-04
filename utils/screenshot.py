# utils/screenshot.py
from mss import mss
import cv2
import numpy as np
from pynput import mouse
import os
from datetime import datetime

# Размер области вокруг курсора
AREA_SIZE = 700

# Папка для сохранения скриншотов
DEBUG_DIR = r"V:\Games\l2BOT\l2tradebot\debug_screenshots"
os.makedirs(DEBUG_DIR, exist_ok=True)


def take_screenshot():
    """
    Делает скриншот области размером AREA_SIZE x AREA_SIZE вокруг курсора мыши.
    Сохраняет изображение в папку debug_screenshots для отладки.
    Возвращает изображение в формате numpy array (BGR), пригодное для OpenCV.
    """
    # Получаем позицию курсора
    mouse_controller = mouse.Controller()
    x, y = mouse_controller.position

    # Границы области
    monitor = {
        "left": x-170,
        "top": y-70,
        "width": AREA_SIZE,
        "height": AREA_SIZE
    }

    # Делаем скриншот
    with mss() as sct:
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Генерируем имя файла с меткой времени
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(DEBUG_DIR, filename)

        # Сохраняем
        cv2.imwrite(filepath, img_bgr)
        print(f"[Screenshot] Сохранён скриншот: {filepath}")

        return img_bgr