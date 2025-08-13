# updater.py
import os
import sys
import requests
import shutil
from config import DB_PATH
from utils.logger import debug_log
from utils.sound import play_notification_sound, play_error_sound
from core.handler import restart_program


# ✅ Правильная ссылка на скачивание
DB_DOWNLOAD_URL = "https://github.com/ShalunZ/l2tradeassistant/releases/download/v1.0/l2trade.db"

def get_remote_db_size():
    """Получает размер файла базы на GitHub"""
    try:
        response = requests.head(DB_DOWNLOAD_URL, timeout=10, allow_redirects=True)
        response.raise_for_status()
        return int(response.headers.get('content-length', 0))
    except Exception as e:
        debug_log(f"❌ Не удалось получить размер удалённой базы: {e}")
        return None

def get_local_db_size():
    """Возвращает размер локальной базы"""
    try:
        return os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    except Exception as e:
        debug_log(f"❌ Ошибка при чтении локальной базы: {e}")
        return 0

def download_db():
    """Скачивает новую базу в temp-файл, затем заменяет старую"""
    temp_path = DB_PATH + ".tmp"
    try:
        debug_log("⏬ Начинаю скачивание обновления базы данных...")
        with requests.get(DB_DOWNLOAD_URL, stream=True, timeout=30, allow_redirects=True) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                f.flush()  # Убедиться, что всё записано
                os.fsync(f.fileno())  # Принудительно сбросить кэш на диск
                debug_log(f"✅ Скачано {downloaded:,} байт")

        # Удаляем старую базу и заменяем
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        os.rename(temp_path, DB_PATH)

        # 🔁 ДОБАВИМ ПРОВЕРКУ: убедимся, что файл существует и не нулевой
        if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
            debug_log("✅ База данных успешно обновлена и готова к использованию!")
            play_notification_sound()
            return True
        else:
            debug_log("❌ Файл базы создан, но пустой или недоступен")
            play_error_sound()
            return False

    except Exception as e:
        debug_log(f"❌ Ошибка при скачивании базы: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        play_error_sound()
        return False

def check_and_update():
    """Проверяет и обновляет базу, если нужно"""
    debug_log("🔍 Проверка обновления базы данных...")

    local_size = get_local_db_size()

    # Если база есть — сравниваем размер
    if local_size > 0:
        remote_size = get_remote_db_size()  # Осторожно: может вернуть None
        if remote_size is None:
            debug_log("⚠️ Не удалось получить размер удалённой базы. Пропускаем проверку.")
        elif local_size == remote_size:
            debug_log("✅ База данных актуальна.")
            return False
        else:
            debug_log(f"🔄 Размер отличается: локальный={local_size}, удалённый={remote_size}")
    else:
        debug_log("🆕 База не найдена. Скачиваю...")

    # Всё равно скачиваем — если нет базы или размер не совпадает
    return download_db()

