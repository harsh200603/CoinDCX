import requests, time, pickle
import numpy as np
import pandas as pd
from tkinter import Tk, StringVar, Label, Button, Frame, BOTH, LEFT, RIGHT, TOP, BOTTOM, X
from tensorflow.keras.models import load_model
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -----------------------------
# Configuration
# -----------------------------
MODEL_PATH = "multi_coin_lstm.keras"
SCALER_PATH = "scaler_close.save"
SEQUENCE_LENGTH = 30
COINS = ["bitcoin", "ethereum", "tether", "ripple"]

BOT_TOKEN = "8366905857:AAGDjpCAU-DGeQ8PIXt_f9ddgJqyMLNMs0o"
CHANNEL_ID = "-1003038471964"

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload, timeout=10)
        print("Telegram response:", res.json())
    except Exception as e:
        print("Telegram error:", e)

# -----------------------------
# Load model & scaler
# -----------------------------
model = load_model(MODEL_PATH)
with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

# -----------------------------
# Live prices from CoinDCX
# -----------------------------
def fetch_live_prices(coin_symbols):
    prices = {}
    url = "https://api.coindcx.com/exchange/ticker"
    data = requests.get(url, timeout=10).json()
    symbol_map = {
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "tether": "USDTUSDT",
        "ripple": "XRPUSDT",
    }
    for coin in coin_symbols:
        for item in data:
            if item.get("market") == symbol_map[coin]:
                prices[coin] = float(item.get("last_price", "0") or 0)
                break
    if "tether" not in prices:
        prices["tether"] = 1.0
    return prices

# -----------------------------
# Tkinter GUI
# -----------------------------
BG = "#0b1220"      # dark cobalt
PANEL = "#0f172a"
FG = "#e5e7eb"
GREEN = "#10b981"
RED = "#ef4444"
ACCENT = "#38bdf8"

class TraderGUI:
    def __init__(self, root):
        self.root = root
        root.title("CoinDCX LSTM Trader — Live & Predicted")
        root.configure(bg=BG)

        # Top info bar
        self.info_var = StringVar(value="Live Prices: —")
        Label(root, textvariable=self.info_var, bg=PANEL, fg=FG,
              font=("Segoe UI", 11), padx=10, pady=8).pack(fill=X, side=TOP)

        # Figures
        self.fig_live = Figure(figsize=(8, 3), facecolor=BG)
        self.ax_live = self.fig_live.add_subplot(111, facecolor=BG)

        self.fig_pred = Figure(figsize=(8, 3), facecolor=BG)
        self.ax_pred = self.fig_pred.add_subplot(111, facecolor=BG)

        frame_charts = Frame(root, bg=BG)
        frame_charts.pack(fill=BOTH, expand=True)
        self.canvas_live = FigureCanvasTkAgg(self.fig_live, master=frame_charts)
        self.canvas_live.get_tk_widget().pack(fill=BOTH, expand=True, side=TOP, pady=4)
        self.canvas_pred = FigureCanvasTkAgg(self.fig_pred, master=frame_charts)
        self.canvas_pred.get_tk_widget().pack(fill=BOTH, expand=True, side=BOTTOM, pady=4)

        # Bottom approval bar
        self.suggest_var = StringVar(value="Suggested Trade: —")
        bar = Frame(root, bg=PANEL)
        bar.pack(fill=X, side=BOTTOM)
        Label(bar, textvariable=self.suggest_var, bg=PANEL, fg=FG,
              font=("Segoe UI", 11)).pack(side=LEFT, padx=10, pady=8)
        Button(bar, text="Approve", command=self.on_approve,
               bg=GREEN, fg="black", relief="flat", padx=16, pady=6).pack(side=RIGHT, padx=8, pady=6)
        Button(bar, text="Reject", command=self.on_reject,
               bg=RED, fg="white", relief="flat", padx=16, pady=6).pack(side=RIGHT, padx=8, pady=6)

        self.last_suggestion = None
        self.update_loop()

    def draw_candles(self, ax, o, h, l, c, title):
        ax.clear()
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG)
        for spine in ax.spines.values():
            spine.set_color(FG)
        ax.set_title(title, color=ACCENT, fontsize=11)

        x = np.arange(len(c))
        for i in range(len(c)):
            color = GREEN if c[i] >= o[i] else RED
            ax.vlines(x[i], l[i], h[i], color=color, linewidth=1)
            ax.add_patch(matplotlib.patches.Rectangle(
                (x[i]-0.3, min(o[i], c[i])),
                0.6,
                abs(c[i]-o[i]) if abs(c[i]-o[i]) > 0 else 0.8,
                facecolor=color, edgecolor=color, linewidth=1
            ))
        ax.grid(alpha=0.15, color="#1f2937")

    def on_approve(self):
        if not self.last_suggestion:
            return
        coin, pct, live_px = self.last_suggestion
        msg = (f"✅ *Trade Alert*\n"
               f"BUY *{coin.upper()}*\n"
               f"Predicted Profit: *{pct:.2f}%*\n"
               f"Current Price: *{live_px:.4f}*")
        send_telegram_message(msg)
        self.suggest_var.set(f"✅ Sent to Telegram: BUY {coin.upper()} (+{pct:.2f}%)")

    def on_reject(self):
        self.suggest_var.set("❌ Trade rejected. Waiting for next update…")

    def update_loop(self):
        try:
            live = fetch_live_prices(COINS)
            live_str = " ".join([f"{k.capitalize()}: {v:.4f}" for k, v in live.items()])
            self.info_var.set(f"Live Prices: {live_str}")

            df = pd.read_csv("crypto_preprocessed.csv", parse_dates=["Date"])
            latest = df.iloc[-SEQUENCE_LENGTH-60:].copy()
            for coin in COINS:
                latest.loc[latest.index[-1], f"{coin.upper()}_Close"] = live.get(
                    coin, latest[f"{coin.upper()}_Close"].iloc[-1]
                )

            features = [f"{c.upper()}_Close" for c in COINS]
            data_scaled = scaler.transform(df[features].values)
            X_input = data_scaled[-SEQUENCE_LENGTH:].reshape(1, SEQUENCE_LENGTH, len(COINS))
            y_scaled = model.predict(X_input, verbose=0)
            y_pred = scaler.inverse_transform(y_scaled)[0]
            predicted = {coin: y_pred[i] for i, coin in enumerate(COINS)}

            tradable = [c for c in COINS if c != "tether"]
            profit = {c: (predicted[c] / live[c] - 1) * 100 for c in tradable if live.get(c, 0) > 0}
            best = max(profit, key=profit.get) if profit else tradable[0]
            self.last_suggestion = (best, profit.get(best, 0.0), live.get(best, 0.0))
            self.suggest_var.set(f"Suggested Trade: BUY {best.upper()} (Pred: {profit.get(best,0):.2f}%)")

            sel = best
            o = latest[f"{sel.upper()}_Open"].to_numpy()
            h = latest[f"{sel.upper()}_High"].to_numpy()
            l = latest[f"{sel.upper()}_Low"].to_numpy()
            c = latest[f"{sel.upper()}_Close"].to_numpy()

            self.draw_candles(self.ax_live, o, h, l, c, f"Live {sel.upper()}")

            o2, h2, l2, c2 = o.copy(), h.copy(), l.copy(), c.copy()
            pred_close = predicted[sel]
            last_close = c2[-1]
            o2 = np.append(o2, last_close)
            c2 = np.append(c2, pred_close)
            hi = max(o2[-1], c2[-1]) * 1.003
            lo = min(o2[-1], c2[-1]) * 0.997
            h2 = np.append(h2, hi)
            l2 = np.append(l2, lo)

            self.draw_candles(self.ax_pred, o2[-60:], h2[-60:], l2[-60:], c2[-60:], f"Predicted {sel.upper()} (next)")

            self.canvas_live.draw()
            self.canvas_pred.draw()

        except Exception as e:
            self.suggest_var.set(f"Error: {e}")

        self.root.after(3000, self.update_loop)

if __name__ == "__main__":
    root = Tk()
    root.configure(bg=BG)
    app = TraderGUI(root)
    root.mainloop()