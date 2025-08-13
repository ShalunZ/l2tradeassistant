# utils/logger.py
import os
import sys
import datetime
import inspect

# Имя файла лога
LOG_FILE = "log.txt"

# Глобальный флаг дебага
DEBUG = True

# Глобальная ссылка на файл
_logfile = None


def _ensure_logfile():
    """Создаёт log.txt, если его нет, и возвращает открытый файловый объект"""
    global _logfile
    if _logfile is None:
        try:
            # Создаёт файл, если не существует, и открывает в режиме 'a' (append)
            _logfile = open(LOG_FILE, 'a', encoding='utf-8')
            # Явно закрываем, чтобы убедиться, что файл создан
            _logfile.close()
            # Открываем снова — на всякий случай
            _logfile = open(LOG_FILE, 'a', encoding='utf-8')
        except Exception as e:
            print(f"❌ Не удалось создать или открыть {LOG_FILE}: {e}")
    return _logfile


def debug_log(message: str, module_name: str = None):
    """
    Централизованная функция логирования.
    :param message: Сообщение для лога
    :param module_name: Имя модуля (автоопределение, если не указано)
    """
    if not DEBUG:
        return

    # Определяем имя модуля
    if module_name is None:
        frame = inspect.currentframe().f_back
        module = frame.f_globals['__name__']
        module_name = module.split('.')[-1]  # Только имя модуля

    # Формируем строку
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{module_name}] {message}\n"

    # Печатаем в консоль
    print(log_entry.rstrip())

    # Пишем в файл, если запущено из .exe
    if hasattr(sys, 'frozen'):
        logfile = _ensure_logfile()
        if logfile:
            try:
                logfile.write(log_entry)
                logfile.flush()
            except Exception as e:
                print(f"❌ Ошибка записи в лог-файл: {e}")


def close_logger():
    """Закрывает файл лога при завершении программы"""
    global _logfile
    if _logfile:
        try:
            _logfile.close()
        except:
            pass
        _logfile = None