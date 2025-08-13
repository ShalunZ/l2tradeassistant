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
AREA_SIZE = 400

# Папка для отладочных скриншотов
DEBUG_DIR = "debug_screenshots"


def enhance_for_ocr(img, attempt=1):
    """
    Улучшает изображение для OCR с вариациями.
    :param img: BGR изображение
    :param attempt: номер попытки (1, 2, 3) — разные настройки
    :return: обработанное BGR изображение
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if attempt == 1:
        # Высокий контраст
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif attempt == 2:
        # Средний контраст, больше резкости
        gray = cv2.GaussianBlur(gray, (1, 1), 1.0)
        gray = cv2.addWeighted(gray, 1.5, gray, -0.5, 0)
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Увеличение
    binary = cv2.resize(binary, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Морфология
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


def take_screenshot(save_debug=False):
    """
    Делает скриншот области вокруг курсора, улучшает его для OCR.
    :param save_debug: Сохранить отладочные изображения
    :return: Улучшенное изображение (BGR), пригодное для OCR
    """
    # Получаем позицию курсора
    mouse_controller = mouse.Controller()
    x, y = mouse_controller.position

    # Границы области
    monitor = {
        "left": x ,
        "top": y - 40,
        "width": AREA_SIZE,
        "height": AREA_SIZE
    }

    # Делаем скриншот
    with mss() as sct:
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)  # BGRA
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Улучшаем изображение для OCR
        img_enhanced = enhance_for_ocr(img_bgr)

        # Сохраняем в папку debug, если нужно
        if save_debug:
            os.makedirs(DEBUG_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_path = os.path.join(DEBUG_DIR, f"screenshot_{timestamp}_original.png")
            enhanced_path = os.path.join(DEBUG_DIR, f"screenshot_{timestamp}_enhanced.png")

            cv2.imwrite(original_path, img_bgr)
            cv2.imwrite(enhanced_path, img_enhanced)
            debug_log(f"📸 Отладочные скриншоты сохранены:\n  {original_path}\n  {enhanced_path}")

        return img_enhanced