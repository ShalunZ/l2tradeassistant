# config.py
import os
import sys

def resource_path(relative_path):
    """ Получает путь к ресурсу, даже если программа запущена из .exe """
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Путь к Tesseract
TESSERACT_PATH = resource_path('tesseract\\tesseract.exe')

# Путь к SQLite
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "l2trade.db")