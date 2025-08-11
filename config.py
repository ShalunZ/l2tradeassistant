# config.py
import os
import sys

def resource_path(relative_path):
    """Возвращает путь к ресурсу, даже если программа запущена из .exe"""
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Путь к Tesseract
TESSERACT_PATH = resource_path('tesseract\\tesseract.exe')

# Путь к SQLite — должен быть ВНЕ _MEIPASS, в папке с .exe
# Используем директорию исполняемого файла
if hasattr(sys, '_MEIPASS'):
    # Если запущено из .exe — ищем data/ рядом с .exe
    executable_dir = os.path.dirname(sys.executable)
else:
    # В режиме разработки — как обычно
    executable_dir = os.path.abspath(".")

DATA_DIR = os.path.join(executable_dir, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "l2trade.db")