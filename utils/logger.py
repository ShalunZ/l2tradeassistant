# utils/logger.py
import os
import sys
import datetime

LOG_FILE = "log.txt"

# Глобальная функция для логирования с временем
def debug_log(message):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

class SafeLogger:
    def __init__(self, stream, logfile):
        self.stream = stream
        self.logfile = logfile

    def write(self, data):
        if data.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {data}"
            if not log_entry.endswith('\n'):
                log_entry += '\n'
            self.logfile.write(log_entry)
            self.logfile.flush()

        if self.stream is not None:
            self.stream.write(data)
            self.stream.flush()

    def flush(self):
        if self.stream is not None:
            self.stream.flush()
        self.logfile.flush()


def setup_logger():
    """Перенаправляет stdout и stderr в файл + сохраняет оригинальные потоки"""
    if hasattr(sys, 'frozen'):  # Если запущен из .exe
        try:
            logfile = open(LOG_FILE, 'a', encoding='utf-8')
        except Exception as e:
            print(f"❌ Не удалось открыть log.txt: {e}")
            logfile = None

        # Оборачиваем stdout и stderr
        if logfile:
            sys.stdout = SafeLogger(sys.stdout, logfile)
            sys.stderr = SafeLogger(sys.stderr, logfile)

        debug_log("🟢 Приложение запущено")
        debug_log(f"📁 Рабочая директория: {os.getcwd()}")