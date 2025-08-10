# database/db.py
import sqlite3
import os
import sys
from config import DB_PATH
from utils.sound import play_error_sound, play_success_sound

# Попробуем импортировать tkinter
try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False


def show_critical_error_and_exit(title, message):
    """Показывает критическое окно с ошибкой и завершает приложение."""
    if HAS_TK:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    else:
        print(f"[FATAL] {title}: {message}")
    sys.exit(1)


def connect_db():
    """Создаёт соединение с SQLite. Возвращает conn или None."""
    if not os.path.exists(DB_PATH):
        error_msg = f"База данных не найдена: {DB_PATH}"
        print(f"[ERROR] {error_msg}")
        show_critical_error_and_exit("Файл базы не найден", error_msg)
        return None

    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Чтобы можно было обращаться к колонкам по имени
        return conn
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к SQLite: {e}")
        show_critical_error_and_exit("Ошибка базы данных", f"Не удалось открыть базу: {e}")
        return None


def test_connection():
    """Проверка подключения к БД."""
    print("🔍 Проверка подключения к базе данных...")
    conn = connect_db()
    if conn is not None:
        try:
            conn.execute("SELECT 1 FROM items LIMIT 1;")
            print("✅ Подключение к базе данных успешно.")
        except Exception as e:
            print(f"❌ Таблица 'items' не найдена: {e}")
            show_critical_error_and_exit("Повреждённая база", "Файл базы существует, но структура повреждена.")
        finally:
            conn.close()


# ⚠️ Убираем save_to_db и ensure_item_exists
# Потому что база read-only — обновляется только через Updater