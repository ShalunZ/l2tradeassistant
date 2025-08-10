# utils/logger.py
import os
import sys
import datetime

LOG_FILE = "log.txt"


def get_log_filename():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"log_{today}.txt"

LOG_FILE = get_log_filename()

def setup_logger():
    """Перенаправляет stdout и stderr в файл + сохраняет оригинальные потоки"""
    if hasattr(sys, 'frozen'):  # Если запущен из .exe
        logfile = open(LOG_FILE, 'a', encoding='utf-8')
        
        class Logger:
            def __init__(self, stream, logfile):
                self.stream = stream
                self.logfile = logfile

            def write(self, data):
                if data.strip():
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"[{timestamp}] {data}"
                    self.logfile.write(log_entry)
                    self.logfile.flush()
                self.stream.write(data)
                self.stream.flush()

            def flush(self):
                self.stream.flush()
                self.logfile.flush()

        sys.stdout = Logger(sys.stdout, logfile)
        sys.stderr = Logger(sys.stderr, logfile)

        # Логируем начало
        print("🟢 Приложение запущено")
        print(f"📁 Рабочая директория: {os.getcwd()}")