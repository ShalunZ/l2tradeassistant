# database/db.py
import psycopg2
import sys
from config import DB_CONFIG
from utils.sound import play_error_sound, play_success_sound

# Попробуем импортировать tkinter
try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False


def show_critical_error_and_exit(title, message):
    """Показывает критическое окно с ошибкой и завершает приложение после подтверждения."""
    if HAS_TK:
        root = tk.Tk()
        root.withdraw()  # Скрываем главное окно
        messagebox.showerror(title, message)
        root.destroy()
    else:
        print(f"[FATAL] {title}: {message}")
    # Завершаем приложение
    sys.exit(1)


def connect_db():
    """Создаёт соединение с PostgreSQL. Возвращает conn или None."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        error_msg = f"\n\n❌Ошибка подключения к Базе Данных:\n\n {e}"
        print(error_msg)
        show_critical_error_and_exit(
            "Критическая ошибка базы данных",
            "Не удалось подключиться к серверу Базе Данных.\n"
            "Приложение не может работать без подключения к базе данных.\n\n"
        )
        return None  # Для надёжности (не достигается из-за sys.exit)


def test_connection():
    """Проверка подключения к БД при запуске модуля."""
    print("🔍 Проверка подключения к базе данных...")
    conn = connect_db()  # Если ошибка — приложение уже закроется
    if conn is not None:
        conn.close()
        print("✅ Подключение к базе данных успешно.")


def save_to_db(item_id, unit_price, quantity, total_price, outlet_type, outlet_city, nickname):
    if not item_id:
        print("❌ Не указан item_id")
        play_error_sound()
        return

    conn = connect_db()  # Если ошибка — приложение закроется здесь
    if conn is None:
        return  # Достигается только если HAS_TK == False, но лучше перестраховаться

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trade_logs (item_id, unit_price, quantity, total_price, outlet_type, outlet_city, nickname, date_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (item_id, unit_price, quantity, total_price, outlet_type, outlet_city, nickname))
            conn.commit()
            print(f"✅ Запись сохранена: item_id={item_id}, тип лавки={outlet_type}, город={outlet_city}, продавец={nickname}, кол-во={quantity}, цена за ед.={unit_price}")
            play_success_sound()
    except Exception as e:
        print(f"❌ Ошибка при сохранении данных: {e}")
        play_error_sound()
    finally:
        try:
            conn.close()
        except:
            pass


def ensure_item_exists(item_id, item_name="Unknown"):
    conn = connect_db()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM items WHERE item_id = %s", (item_id,))
            if cur.fetchone():
                print(f"🔁 Предмет с item_id={item_id} уже существует")
                return

            cur.execute("""
                INSERT INTO items (item_id, item_name)
                VALUES (%s, %s)
            """, (item_id, item_name))
            conn.commit()
            print(f"🆕 Предмет добавлен: {item_id} → {item_name}")
    except Exception as e:
        print(f"❌ Ошибка при добавлении предмета: {e}")
        play_error_sound()
    finally:
        try:
            conn.close()
        except:
            pass


# 🔁 Проверка подключения при импорте модуля
if __name__ != "__main__":
    test_connection()