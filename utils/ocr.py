# utils/ocr.py
import cv2
import pytesseract
from config import TESSERACT_PATH
import numpy as np  # <-- Добавлено!

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extract_text_from_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    scale_percent = 200
    width = int(thresh.shape[1] * scale_percent / 100)
    height = int(thresh.shape[0] * scale_percent / 100)
    resized = cv2.resize(thresh, (width, height), interpolation=cv2.INTER_LINEAR)
    kernel = np.ones((1, 1), np.uint8)
    resized = cv2.erode(resized, kernel, iterations=1)
    resized = cv2.dilate(resized, kernel, iterations=1)
    text = pytesseract.image_to_string(resized, lang='eng')
    return text