import requests
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import pickle
import time

# -----------------------------
# Configuration
# -----------------------------
MODEL_PATH = "multi_coin_lstm.keras"    # Your trained LSTM model
SCALER_PATH = "scaler_close.save"       # Saved MinMaxScaler for close prices
SEQUENCE_LENGTH = 30                    # Last 30 days used in training
COINS = ["bitcoin", "ethereum", "tether", "ripple"]  # Coins to consider

# Telegram configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"   # your bot token
CHANNEL_ID = "-1003038471964"   # numeric channel ID

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    print("Telegram response:", response.json())

# -----------------------------
# Load Model and Scaler
# -----------------------------
model = load_model(MODEL_PATH)
with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

# -----------------------------
# Fetch Live CoinDCX Data
# -----------------------------
def fetch_live_prices(coin_symbols):
    prices = {}
    url = "https://api.coindcx.com/exchange/ticker"
    response = requests.get(url)
    data = response.json()

    symbol_map = {
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "tether": "USDTUSDT",
        "ripple": "XRPUSDT"
    }

    for coin in coin_symbols:
        for item in data:
            if item['market'] == symbol_map[coin]:
                prices[coin] = float(item['last_price'])
    # If tether is missing, set to 1.0
    if "tether" not in prices:
        prices["tether"] = 1.0
    return prices

# -----------------------------
# Main Loop for Live Trading Suggestion
# -----------------------------
while True:
    live_prices = fetch_live_prices(COINS)

    # 🔹 Print nicely formatted current prices
    print("\nCurrent Live Prices:")
    for coin, price in live_prices.items():
        print(f"{coin.capitalize()}: {price:.6f}")

    # Load historical dataset
    df = pd.read_csv("crypto_preprocessed.csv", parse_dates=["Date"])
    latest_row = df.iloc[-1:].copy()

    # Append live prices to latest row
    for coin in COINS:
        latest_row[f"{coin.upper()}_Close"] = live_prices.get(coin, latest_row[f"{coin.upper()}_Close"].values[0])

    df = pd.concat([df, latest_row], ignore_index=True)

    # Select only close prices for scaling
    features = [f"{coin.upper()}_Close" for coin in COINS]
    data = df[features].values
    data_scaled = scaler.transform(data)

    # Prepare sequence for prediction
    X_input = data_scaled[-SEQUENCE_LENGTH:].reshape(1, SEQUENCE_LENGTH, len(COINS))

    # Predict next prices
    y_pred_scaled = model.predict(X_input)
    y_pred_rescaled = scaler.inverse_transform(y_pred_scaled)
    predicted_prices = {coin: y_pred_rescaled[0, idx] for idx, coin in enumerate(COINS)}

    # 🔹 Print nicely formatted predicted prices
    print("\nPredicted Next Prices:")
    for coin, price in predicted_prices.items():
        print(f"{coin.capitalize()}: {price:.6f}")

    # Suggest most profitable trade (skip tether)
    tradable_coins = [coin for coin in COINS if coin != "tether"]
    profit_pct = {coin: (predicted_prices[coin] / live_prices[coin] - 1) * 100
                  for coin in tradable_coins}
    best_coin = max(profit_pct, key=profit_pct.get)

    print(f"\nSuggested Trade: BUY {best_coin.upper()} (Predicted Profit: {profit_pct[best_coin]:.2f}%)")

    # Ask user for approval
    decision = input("Do you want to execute this trade? (yes/no): ").strip().lower()
    if decision == "yes":
        # Send Telegram message
        msg = (
            f"✅ Trade Alert: BUY {best_coin.upper()}\n"
            f"Predicted Profit: {profit_pct[best_coin]:.2f}%\n"
            f"Current Price: {live_prices[best_coin]:.2f}"
        )
        send_telegram_message(msg)
        print("Telegram message sent!")
        # continue loop instead of breaking
    else:
        print("❌ Trade not approved. Updating prices for next suggestion...")

    # Short delay before next update
    time.sleep(3)
