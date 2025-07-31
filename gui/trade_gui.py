# gui/trade_gui.py

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, Frame, Label, Entry, Button, Canvas, Scrollbar, Toplevel
from PIL import Image, ImageTk
import io
import winsound
from database.db import connect_db
from io import BytesIO
from utils.sound import play_error_sound, play_success_sound




previous_choice = [0, 0]  # [тип лавки (0 покупка /1 продажа), индекс города]


class TradeLoggerGUI:
    def __init__(self, root):
        self.root = root
        global previous_choice

    def show_confirmation_dialog(self, data):
        print("DEBUG: Полученные данные:", data)

        dialog = tk.Toplevel(self.root)
        dialog.overrideredirect(True)
        dialog.title("Подтверждение")
        dialog.geometry("500x650+100+50")
        dialog.configure(bg="#2a2a2a")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        dialog.focus_force()
        dialog.update()

        # --- Заголовок ---
        header_frame = tk.Frame(dialog, bg="#1e1e1e", height=40)
        header_frame.pack(fill="x", padx=10, pady=(5, 10))
        header_frame.pack_propagate(False)
        tk.Label(
            header_frame,
            text="🔍 Найдена лавка",
            font=("Segoe UI", 12, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        ).pack(pady=8)

        # --- Информационная панель ---
        info_frame = tk.Frame(dialog, bg="#2a2a2a", relief="flat", bd=0)
        info_frame.pack(fill="x", padx=20, pady=5)

        # Получаем имя предмета из БД
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT item_name FROM items WHERE item_id = %s", (data["item_id"],))
            result = cur.fetchone()
            conn.close()
            item_name_db = result[0] if result else "Неизвестно"
            is_known = bool(result)
        except Exception as e:
            print(f"⚠️ Ошибка при получении имени из БД: {e}")
            item_name_db = "Неизвестно"
            is_known = False

        # Формируем основную информацию
        info_text = (
            f"  ID: {data['item_id']}\n"
            f"  Предмет: {item_name_db}\n"
            f"  Цена за ед.: {data['unit_price']:,} Adena\n"
            f"  Кол-во: {data['quantity']}\n"
            f"  Сумма: {data['total_price']:,} Adena"
        )

        tk.Label(
            info_frame,
            text=info_text,
            justify="left",
            font=("Consolas", 10),
            bg="#2a2a2a",
            fg="#e0e0e0",
            anchor="w",
            padx=10,
            pady=10
        ).pack(fill="x")

        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)

        # --- Аналитика: Сравнение с рынком ---
        analytics_frame = tk.Frame(dialog, bg="#2a2a2a")
        analytics_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(
            analytics_frame,
            text="📊 СРАВНЕНИЕ С РЫНКОМ",
            font=("Segoe UI", 10, "bold"),
            bg="#2a2a2a",
            fg="#00BFFF"
        ).pack(anchor="w", pady=(0, 10))

        # Пытаемся получить статистику из БД
        try:
            conn = connect_db()
            cur = conn.cursor()

            outlet_type = data.get("outlet_type")  # 0 = Продажа, 1 = Покупка

            if outlet_type == 0:  # Продажа → сравниваем с другими продажами
                cur.execute("""
                    SELECT 
                        AVG(unit_price)::float AS avg_price,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unit_price) AS median_price
                    FROM trade_logs 
                    WHERE item_id = %s AND outlet_type = 0 AND date_timestamp >= NOW() - INTERVAL '7 days'
                """, (data["item_id"],))
            else:  # Покупка → сравниваем с другими покупками
                cur.execute("""
                    SELECT 
                        AVG(unit_price)::float AS avg_price,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unit_price) AS median_price
                    FROM trade_logs 
                    WHERE item_id = %s AND outlet_type = 1 AND date_timestamp >= NOW() - INTERVAL '7 days'
                """, (data["item_id"],))

            row = cur.fetchone()
            conn.close()

            if row and row[0] is not None:
                avg_price = float(row[0])
                median_price = float(row[1])
                current_price = float(data["unit_price"])

                # Определяем выгодность
                if outlet_type == 0:  # Продажа: чем выше, тем лучше
                    if current_price >= avg_price * 1.1:
                        flag = "🟢"
                        verdict = "Высокая цена! Лучше среднего"
                        color = "#4CAF50"
                    elif current_price <= avg_price * 0.9:
                        flag = "🔴"
                        verdict = "Низкая цена. Могут не купить"
                        color = "#F44336"
                    else:
                        flag = "🟡"
                        verdict = "Средняя цена. Нормально"
                        color = "#FF9800"
                else:  # Покупка: чем ниже, тем лучше
                    if current_price <= avg_price * 0.9:
                        flag = "🟢"
                        verdict = "Низкая цена! Выгодно купить"
                        color = "#4CAF50"
                    elif current_price >= avg_price * 1.1:
                        flag = "🔴"
                        verdict = "Высокая цена. Переплата"
                        color = "#F44336"
                    else:
                        flag = "🟡"
                        verdict = "Средняя цена. Можно рассмотреть"
                        color = "#FF9800"

                # Формируем текст аналитики
                analysis_text = (
                    f"{flag} {verdict}\n\n"
                    f"Средняя цена: {avg_price:,.0f} Adena\n"
                    f"Медиана: {median_price:,.0f} Adena\n"
                    f"Ваша цена: {current_price:,.0f} Adena\n"
                    f"Отклонение: {((current_price - avg_price) / avg_price * 100):+.1f}%"
                )

            else:
                analysis_text = "📊 Недостаточно данных для анализа.\nПока нет истории по этому предмету."
                color = "#bbbbbb"

        except Exception as e:
            print(f"⚠️ Ошибка при получении аналитики: {e}")
            analysis_text = "❌ Не удалось загрузить аналитику.\nБаза данных недоступна."
            color = "#d32f2f"

        # Отображаем анализ
        tk.Label(
            analytics_frame,
            text=analysis_text,
            justify="left",
            font=("Consolas", 10),
            bg="#2a2a2a",
            fg=color,
            anchor="w",
            padx=10,
            pady=10
        ).pack(fill="x")

        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)

        # --- Форма ввода ---
        form_frame = tk.Frame(dialog, bg="#2a2a2a", bd=3)
        form_frame.pack(fill="x", padx=20)

        # Тип лавки
        tk.Label(form_frame, text="Тип лавки:", font=("Segoe UI", 9), bg="#2a2a2a", fg="#bbbbbb").pack()
        outlet_var = tk.StringVar()
        outlet_combo = ttk.Combobox(form_frame, textvariable=outlet_var, state="readonly", width=15, font=("Segoe UI", 9))
        outlet_combo['values'] = ("Покупка", "Продажа")
        if "outlet_type" in data:
            outlet_combo.current(data["outlet_type"])
        else:
            outlet_combo.current(0)
        outlet_combo.pack(pady=(0, 10))

        # Город
        tk.Label(form_frame, text="Город:", font=("Segoe UI", 9), bg="#2a2a2a", fg="#bbbbbb").pack()
        city_var = tk.StringVar()
        city_combo = ttk.Combobox(form_frame, textvariable=city_var, state="readonly", width=25, font=("Segoe UI", 9))
        city_combo['values'] = (
            "Talking Island Village", "Elven Village", "The Dark Elf Village", "Orc Village", "Dwarven Village",
            "The Village of Gludin", "The Town of Gludio", "The Town of Dion", "Giran Castle Town",
            "Town of Oren", "Heine", "Town of Aden", "Floran Village", "Hunters Village",
            "Ivory Tower", "Gludin Arena", "Giran Arena", "Coliseum"
        )
        city_combo.current(previous_choice[1] if previous_choice else 0)
        city_combo.pack(pady=(0, 10))

        # Никнейм продавца
        seller_name = data.get("seller_name", "").strip()
        if not seller_name or seller_name == "Unknown":
            seller_name = "(неизвестно)"

        tk.Label(
            form_frame,
            text="Никнейм продавца: ",
            font=("Segoe UI", 9),
            bg="#2a2a2a",
            fg="#bbbbbb"
        ).pack()

        tk.Label(
            form_frame,
            text=seller_name,
            font=("Segoe UI", 9, "bold"),
            bg="#2a2a2a",
            fg="#ffffff"
        ).pack()

        nick_name = tk.StringVar(value=seller_name)
        nickname_entry = tk.Entry(
            form_frame,
            textvariable=nick_name,
            width=25,
            font=("Segoe UI", 10),
            bg="#3a3a3a",
            fg="#ffffff",
            insertbackground="white",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#555"
        )
        nickname_entry.pack()
        nickname_entry.focus_set()

        # Название предмета (если неизвестно)
        item_name_var = None
        item_name_entry = None
        if not is_known:
            tk.Label(form_frame, text="Название предмета:", font=("Segoe UI", 9), bg="#2a2a2a", fg="#bbbbbb").pack()
            item_name_var = tk.StringVar()
            item_name_entry = tk.Entry(
                form_frame, textvariable=item_name_var, width=25,
                font=("Segoe UI", 10),
                bg="#3a3a3a", fg="#ffffff", insertbackground="white",
                relief="flat", highlightthickness=1, highlightbackground="#555"
            )
            item_name_entry.pack(pady=(0, 10))
            item_name_entry.insert(0, data.get("item_name", "Новое название"))

        # --- Подсказки ---
        tips_frame = tk.Frame(dialog, bg="#252525", relief="flat", bd=1)
        tips_frame.pack(fill="x", padx=20, pady=(10, 5), ipady=5)
        tk.Label(
            tips_frame,
            text="ℹ️ Enter — Подтвердить  |  Esc — Отмена",
            font=("Segoe UI", 8),
            bg="#252525",
            fg="#aaaaaa"
        ).pack()

        # --- Кнопки ---
        button_frame = tk.Frame(dialog, bg="#2a2a2a")
        button_frame.pack(pady=15)

        def confirm():
            selected_outlet = outlet_combo.get()
            selected_city_index = city_combo.current()
            entered_nickname = nickname_entry.get().strip()

            if not selected_outlet or not entered_nickname:
                entered_nickname = seller_name

            data["outlet_type"] = 0 if selected_outlet == "Покупка" else 1
            data["outlet_city"] = selected_city_index
            data["nickname"] = entered_nickname

            if item_name_entry is not None:
                entered_item_name = item_name_entry.get().strip()
                if not entered_item_name or entered_item_name == "Новое название":
                    play_error_sound()
                    messagebox.showwarning("Ошибка", "Введите корректное название предмета!")
                    return
                data["item_name"] = entered_item_name
                from database.db import ensure_item_exists
                ensure_item_exists(data["item_id"], entered_item_name)

            from database.db import save_to_db
            save_to_db(
                item_id=data["item_id"],
                unit_price=data["unit_price"],
                quantity=data["quantity"],
                total_price=data["total_price"],
                outlet_type=data["outlet_type"],
                outlet_city=data["outlet_city"],
                nickname=data["nickname"]
            )

            global previous_choice
            previous_choice = [data["outlet_type"], selected_city_index]

            dialog.destroy()
            play_success_sound()

        def cancel():
            dialog.destroy()
            play_error_sound()

        tk.Button(
            button_frame, text="✅ Подтвердить", command=confirm,
            bg="#007acc", fg="white", font=("Segoe UI", 10), relief="flat", padx=20, pady=6,
            activebackground="#005a9e", cursor="hand2"
        ).pack(side="left", padx=10)

        tk.Button(
            button_frame, text="❌ Отмена", command=cancel,
            bg="#d32f2f", fg="white", font=("Segoe UI", 10), relief="flat", padx=20, pady=6,
            activebackground="#b71c1c", cursor="hand2"
        ).pack(side="left", padx=10)

        # --- Горячие клавиши ---
        dialog.bind('<Return>', lambda e: confirm())
        dialog.bind('<Escape>', lambda e: cancel())

        self.root.wait_window(dialog)


    def show_deal_info(self, data):
        """
        Показывает окно с информацией о лучших сделках по item_id.
        Новый макет: лево-право, центрированное название, нижний блок с профитом.
        """
        item_id = data.get("item_id")
        if not item_id:
            play_error_sound()
            messagebox.showerror("Ошибка", "Не указан item_id")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"📊 Информация по item_id {item_id}")
        dialog.geometry("460x460+100+100")
        dialog.configure(bg="#2a2a2a")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        dialog.focus_force()
        dialog.update()

        # --- Заголовок: Название предмета ---
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT item_name FROM items WHERE item_id = %s", (item_id,))
            result = cur.fetchone()
            conn.close()
            item_name = result[0] if result else f"Предмет {item_id}"
        except:
            item_name = f"Предмет {item_id}"

        header_frame = tk.Frame(dialog, bg="#1e1e1e", height=60)
        header_frame.pack(fill="x", padx=20, pady=(10, 15))
        header_frame.pack_propagate(False)
        tk.Label(
            header_frame,
            text=item_name.upper(),
            font=("Segoe UI", 14, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        ).pack(expand=True)

        # --- Основной контейнер: лево-право-центр ---
        main_frame = tk.Frame(dialog, bg="#2a2a2a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Левый блок: Лучшая покупка
        left_frame = tk.Frame(main_frame, bg="#2e2e2e", relief="groove", bd=1, padx=15, pady=15)
        left_frame.pack(side="left", fill="both")

        tk.Label(
            left_frame,
            text="🟢 ЛУЧШАЯ ПОКУПКА",
            font=("Segoe UI", 9, "bold"),
            bg="#2e2e2e",
            fg="#4CAF50"
        ).pack(anchor="w", pady=(0, 10))

        # Данные
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT best_buy_price::float, best_buy_nickname, best_buy_city_name, buy_hours_ago
                FROM vw_trade_deals WHERE item_id = %s
            """, (item_id,))
            row = cur.fetchone()
            conn.close()

            if row:
                price, nickname, city, hours_ago = row
                price_text = f"{int(price):,}" if price else "—"
                nickname_text = nickname or "—"
                city_text = city or "—"
                age_text = f"{hours_ago:.1f} ч" if hours_ago else "—"
            else:
                price_text = nickname_text = city_text = age_text = "—"
        except Exception as e:
            print(f"⚠️ Ошибка БД: {e}")
            price_text = nickname_text = city_text = age_text = "—"

        buy_info = f"Цена: {price_text} Adena\nКто: {nickname_text}\nГород: {city_text}\nВозраст: {age_text}"
        tk.Label(
            left_frame,
            text=buy_info,
            justify="left",
            font=("Consolas", 8),
            bg="#2e2e2e",
            fg="#e0e0e0",
            anchor="w"
        ).pack(anchor="w", pady=5)

        # Правый блок: Лучшая продажа
        right_frame = tk.Frame(main_frame, bg="#2e2e2e", relief="groove", bd=1, padx=15, pady=15)
        right_frame.pack(side="right", fill="both")

        tk.Label(
            right_frame,
            text="🔴 ЛУЧШАЯ ПРОДАЖА",
            font=("Segoe UI", 9, "bold"),
            bg="#2e2e2e",
            fg="#F44336"
        ).pack(anchor="w", pady=(0, 10))

        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT best_sell_price::float, best_sell_nickname, best_sell_city_name, sell_hours_ago
                FROM vw_trade_deals WHERE item_id = %s
            """, (item_id,))
            row = cur.fetchone()
            conn.close()

            if row:
                price, nickname, city, hours_ago = row
                price_text = f"{int(price):,}" if price else "—"
                nickname_text = nickname or "—"
                city_text = city or "—"
                age_text = f"{hours_ago:.1f} ч" if hours_ago else "—"
            else:
                price_text = nickname_text = city_text = age_text = "—"
        except:
            price_text = nickname_text = city_text = age_text = "—"

        sell_info = f"Цена: {price_text} Adena\nКто: {nickname_text}\nГород: {city_text}\nВозраст: {age_text}"
        tk.Label(
            right_frame,
            text=sell_info,
            justify="left",
            font=("Consolas", 8),
            bg="#2e2e2e",
            fg="#e0e0e0",
            anchor="w"
        ).pack(anchor="w", pady=5)

        # --- Нижний блок: Профит, статистика, рекомендации ---
        bottom_frame = tk.Frame(dialog, bg="#252525", relief="flat", bd=1, padx=15, pady=15)
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))

        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT profit_abs, profit_percent, avg_buy_price, avg_sell_price
                FROM vw_trade_deals WHERE item_id = %s
            """, (item_id,))
            row = cur.fetchone()
            conn.close()

            if row:
                profit_abs, profit_percent, avg_buy, avg_sell = row
                profit_abs = float(profit_abs) if profit_abs else 0
                profit_percent = float(profit_percent) if profit_percent else 0
            else:
                profit_abs = profit_percent = 0
        except:
            profit_abs = profit_percent = 0

        # Иконка и цвет в зависимости от профита
        if profit_percent >= 20:
            icon = "🚀"
            color = "#4CAF50"
            tip = "Отличный профит! Идеально для перепродажи."
        elif profit_percent >= 5:
            icon = "💰"
            color = "#FF9800"
            tip = "Умеренный профит. Можно рассмотреть."
        else:
            icon = "📉"
            color = "#F44336"
            tip = "Низкий профит. Вряд ли выгодно."

        bottom_text = f"{icon} Потенциальный профит: {profit_abs:,.0f} Adena ({profit_percent:.1f}%)\n\n"
        bottom_text += f"💡 Рекомендация: {tip}"

        tk.Label(
            bottom_frame,
            text=bottom_text,
            justify="left",
            font=("Segoe UI", 8),
            bg="#252525",
            fg=color
        ).pack(anchor="w")

        # --- Кнопка ---
        btn_frame = tk.Frame(dialog, bg="#2a2a2a")
        btn_frame.pack(pady=5)

        def close():
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="✅ Закрыть",
            command=close,
            bg="#007acc",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            padx=20,
            pady=6,
            activebackground="#005a9e",
            cursor="hand2"
        ).pack()

        # --- Горячие клавиши ---
        dialog.bind('<Return>', lambda e: close())
        dialog.bind('<Escape>', lambda e: close())

        self.root.wait_window(dialog)