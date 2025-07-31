import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from database.db import connect_db

def show_item_details(self, item_id, item_name):
    detail_dialog = Toplevel(self.root)
    detail_dialog.geometry("1000x600+100+50")
    detail_dialog.title(f"Статистика: {item_name}")
    detail_dialog.configure(bg="#1e1e1e")
    detail_dialog.grab_set()

    Label(detail_dialog, text=f"Статистика по: {item_name} ({item_id})", font=("Arial", 14),
          bg="#1e1e1e", fg="#dddddd").pack(pady=10)

    # --- Запрос данных ---
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT date_timestamp, unit_price, outlet_type
        FROM trade_logs
        WHERE item_id = %s
        ORDER BY date_timestamp DESC
        LIMIT 30
    """, (str(item_id),))
    result = cur.fetchall()
    conn.close()

    if not result:
        Label(detail_dialog, text="Нет данных о ценах", bg="#1e1e1e", fg="#777777").pack(pady=20)
        return

    df = pd.DataFrame(result, columns=["date", "price", "type"])
    df['type'] = df['type'].map({0: "Покупка", 1: "Продажа"})
    df['date'] = pd.to_datetime(df['date'])

    # --- Группируем по дням ---
    daily_prices = df.groupby([df["date"].dt.date, 'type']).agg({'price': 'mean'}).reset_index()
    daily_prices.columns = ["date", "type", "avg_price"]

    buy_data = daily_prices[daily_prices["type"] == "Покупка"]
    sell_data = daily_prices[daily_prices["type"] == "Продажа"]

    # --- График ---
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#2e2e2e')
    ax.tick_params(colors='white')
    ax.set_title("Цены покупки и продажи по дням", color="white")
    ax.set_xlabel("Дата", color="white")
    ax.set_ylabel("Цена", color="white")

    if not buy_data.empty:
        ax.plot(buy_data["date"], buy_data["avg_price"], label="Покупка", color="#ff9999", marker="o")
    if not sell_data.empty:
        ax.plot(sell_data["date"], sell_data["avg_price"], label="Продажа", color="#66b3ff", marker="o")

    ax.legend(loc="upper left", facecolor='#2e2e2e', edgecolor='none')
    ax.grid(True, color="#444444")

    canvas = FigureCanvasTkAgg(fig, master=detail_dialog)
    canvas.get_tk_widget().pack(pady=10, padx=20)

    # --- Статистика и прогноз ---
    stats_frame = Frame(detail_dialog, bg="#2e2e2e")
    stats_frame.pack(fill="x", padx=20, pady=10)

    # Среднее, медиана, мин/макс
    if not buy_data.empty:
        avg_buy = buy_data["avg_price"].mean()
        median_buy = buy_data["avg_price"].median()
        min_buy = buy_data["avg_price"].min()
        max_buy = buy_data["avg_price"].max()
    else:
        avg_buy = median_buy = min_buy = max_buy = "—"

    if not sell_data.empty:
        avg_sell = sell_data["avg_price"].mean()
        median_sell = sell_data["avg_price"].median()
        min_sell = sell_data["avg_price"].min()
        max_sell = sell_data["avg_price"].max()
    else:
        avg_sell = median_sell = min_sell = max_sell = "—"

    stats_text = (
        f"📊 Средняя цена покупки: {avg_buy}\n"
        f"📉 Медианная цена покупки: {median_buy}\n"
        f"🟢 Мин./Макс. цена покупки: {min_buy} – {max_buy}\n\n"
        f"📊 Средняя цена продажи: {avg_sell}\n"
        f"📈 Медианная цена продажи: {median_sell}\n"
        f"🟢 Мин./Макс. цена продажи: {min_sell} – {max_sell}"
    )

    Label(stats_frame, text=stats_text, justify="left", font=("Arial", 10),
          bg="#2e2e2e", fg="#cccccc", padx=10, pady=10).pack(side="left", fill="y")

    Button(detail_dialog, text="Закрыть", command=detail_dialog.destroy,
           bg="#3a3a3a", fg="#ffffff", width=10).pack(pady=10)

    detail_dialog.wait_window()