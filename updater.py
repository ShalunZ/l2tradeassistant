# updater.py
import os
import time
from utils.sound import play_notification_sound
from config import DB_PATH

def get_local_version():
    """Возвращает MD5 хеш локальной базы, если файл существует."""
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "rb") as f:
                data = f.read()
                # Простой "хеш" — длина + время изменения
                return f"{len(data)}_{os.path.getmtime(DB_PATH):.0f}"
        except Exception:
            return "unknown"
    return None

def get_remote_version():
    """
    Заглушка: возвращает фиктивную версию.
    В реальной версии будет запрашивать version.json с сервера.
    """
    print("⚠️ Updater: Режим заглушки. Нет подключения к удалённому серверу.")
    # Имитируем, что удалённая версия всегда совпадает с локальной
    return get_local_version() or "1"

def download_db():
    """
    Заглушка: не скачивает ничего.
    В реальной версии будет загружать l2trade.db с GitHub.
    """
    print("⚠️ Updater: Скачивание отключено (заглушка).")
    return False

def check_and_update():
    """
    Проверяет, нужно ли обновить базу.
    Сейчас всегда возвращает False — работает с локальной копией.
    """
    print("🔍 Updater: Проверка обновления базы данных... (заглушка)")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Файл базы не найден: {DB_PATH}")
        print("🛑 Работа остановлена. Поместите тестовую базу вручную.")
        return False

    print(f"✅ Используется локальная база: {DB_PATH}")
    print(f"ℹ️  Для обновления замените файл вручную.")
    play_notification_sound()
    return False  # Никаких изменений