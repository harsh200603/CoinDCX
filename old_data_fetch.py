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

    # Fetch 365 days OHLCV-like data
    ohlc_url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    ohlc_params = {
        'vs_currency': 'usd',
        'days': 365,          # last 1 year
        'interval': 'daily'
    }
    ohlc_data = requests.get(ohlc_url, params=ohlc_params).json()

    prices = ohlc_data.get("prices", [])
    market_caps = ohlc_data.get("market_caps", [])
    total_volumes = ohlc_data.get("total_volumes", [])

    df = pd.DataFrame({
        "Date": [datetime.fromtimestamp(p[0]/1000) for p in prices],
        "Open": [p[1] for p in prices],
        "High": [p[1] for p in prices],
        "Low": [p[1] for p in prices],
        "Close": [p[1] for p in prices],
        "Market Cap": [mc[1] for mc in market_caps],
        "Total Volume": [tv[1] for tv in total_volumes]
    })

    # Save each coin as CSV
    file_name = f"{coin}_1yr_OHLCV.csv"
    df.to_csv(file_name, index=False)
    print(f"✅ Saved {file_name}")

print("All top 5 coins data fetched successfully!")