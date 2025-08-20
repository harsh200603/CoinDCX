import pandas as pd
from functools import reduce

# List of CSV files
coins_files = [
    "bitcoin_1yr_OHLCV.csv",
    "ethereum_1yr_OHLCV.csv",
    "tether_1yr_OHLCV.csv",
    "ripple_1yr_OHLCV.csv"
]

dfs = []
for file in coins_files:
    df = pd.read_csv(file)
    df["Date"] = pd.to_datetime(df["Date"])

    # Extract coin name from filename for column renaming
    coin_name = file.split("_")[0].upper()

    df = df.rename(columns={
        "Open": f"{coin_name}_Open",
        "High": f"{coin_name}_High",
        "Low": f"{coin_name}_Low",
        "Close": f"{coin_name}_Close",
        "Market Cap": f"{coin_name}_MarketCap",
        "Total Volume": f"{coin_name}_Volume"
    })

    dfs.append(df)

# Merge all DataFrames on Date
combined_df = reduce(lambda left, right: pd.merge(left, right, on="Date", how="outer"), dfs)

# Sort by Date and fill missing values
combined_df = combined_df.sort_values("Date").ffill().bfill()

# Save combined CSV
combined_df.to_csv("crypto_top5_1yr_combined.csv", index=False)

print("✅ Combined CSV saved: crypto_top5_1yr_combined.csv")
print(combined_df.head())