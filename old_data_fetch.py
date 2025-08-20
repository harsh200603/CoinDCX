import requests
import pandas as pd
from datetime import datetime

# Get top 5 coins from CoinGecko
top_coins_url = "https://api.coingecko.com/api/v3/coins/markets"
params = {
    'vs_currency': 'usd',
    'order': 'market_cap_desc',
    'per_page': 5,
    'page': 1
}
coins_data = requests.get(top_coins_url, params=params).json()
top_coins = [coin['id'] for coin in coins_data]
print("Top 5 coins:", top_coins)

for coin in top_coins:
    print(f"Fetching 1 year data for {coin}...")

    if coin in ["bitcoin","ethereum"]:
        # Use OHLC endpoint (true OHLC data)
        ohlc_url = f"https://api.coingecko.com/api/v3/coins/{coin}/ohlc"
        ohlc_params = {'vs_currency': 'usd', 'days': 365}
        ohlc_data = requests.get(ohlc_url, params=ohlc_params).json()

        df = pd.DataFrame(ohlc_data, columns=["Timestamp", "Open", "High", "Low", "Close"])
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df = df[["Date", "Open", "High", "Low", "Close"]]

    else:
        # For other coins, use market_chart and build OHLC from daily prices
        ohlc_url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
        ohlc_params = {'vs_currency': 'usd', 'days': 365, 'interval': 'daily'}
        ohlc_data = requests.get(ohlc_url, params=ohlc_params).json()

        prices = ohlc_data.get("prices", [])
        df = pd.DataFrame(prices, columns=["Timestamp", "Price"])
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Date", inplace=True)

        # Derive OHLC per day
        df = df.resample("1D").agg({"Price": ["first", "max", "min", "last"]})
        df.columns = ["Open", "High", "Low", "Close"]
        df.reset_index(inplace=True)

    # Save each coin as CSV
    file_name = f"{coin}_1yr_OHLC.csv"
    df.to_csv(file_name, index=False)
    print(f"✅ Saved {file_name}")

print("All top 5 coins data fetched successfully!")