# utils/screenshot.py
from mss import mss
import cv2
import numpy as np
from pynput import mouse
import os
from datetime import datetime
from config import resource_path
from utils.logger import debug_log

# Размер области вокруг курсора
AREA_SIZE = 700

# Папка для отладочных скриншотов
DEBUG_DIR = "debug_screenshots"



def take_screenshot(save_debug=False):
    """
    Делает скриншот области размером AREA_SIZE x AREA_SIZE вокруг курсора мыши.
    
    :param save_debug: Если True — сохраняет оригинальный и увеличенный скриншот в debug_screenshots
    :return: Увеличенное в 2 раза изображение (BGR), пригодное для OpenCV
    """
    # Получаем позицию курсора
    mouse_controller = mouse.Controller()
    x, y = mouse_controller.position

    # Границы области
    monitor = {
        "left": x - 100,
        "top": y - 70,
        "width": AREA_SIZE,
        "height": AREA_SIZE
    }

    # Делаем скриншот
    with mss() as sct:
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)  # BGRA
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Увеличиваем изображение в 2 раза
        img_resized = cv2.resize(
            img_bgr,
            (AREA_SIZE * 2, AREA_SIZE * 2),
            interpolation=cv2.INTER_CUBIC  # Лучшее качество для увеличения
        )

        # Сохраняем в папку debug, если нужно
        if save_debug:
            os.makedirs(DEBUG_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_path = os.path.join(DEBUG_DIR, f"screenshot_{timestamp}_original.png")
            resized_path = os.path.join(DEBUG_DIR, f"screenshot_{timestamp}_x2.png")

            cv2.imwrite(original_path, img_bgr)
            cv2.imwrite(resized_path, img_resized)
            debug_log(f"📸 Отладочные скриншоты сохранены:\n  {original_path}\n  {resized_path}")

        return img_resized