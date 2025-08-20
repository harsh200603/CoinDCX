import yfinance as yf
import pandas as pd

# Example: Fetch BTC/USDT data from Yahoo Finance
# BTC-USD works for Bitcoin vs USD (use ETH-USD, etc. for other cryptos)
symbol = "BTC-USD"

# Fetch last 1 year of 1-day OHLCV data
df = yf.download(symbol, period="1y", interval="1d")

# Reset index (date as column)
df.reset_index(inplace=True)

# Rename columns to match OHLCV format
df.rename(columns={
    "Date": "Date",
    "Open": "Open",
    "High": "High",
    "Low": "Low",
    "Close": "Close",
    "Volume": "Volume"
}, inplace=True)

# Add Market Cap column (optional: Not available directly from yfinance)
df["Market Cap"] = df["Close"] * df["Volume"]

# Show the first 10 rows
print(df.head(10))

# Save to CSV for further use
df.to_csv("btc_ohlcv.csv", index=False)
print("\n✅ Data saved to btc_ohlcv.csv")