import requests

BOT_TOKEN = "8366905857:AAGDjpCAU-DGeQ8PIXt_f9ddgJqyMLNMs0o"
CHANNEL_ID = "-1003038471964"  # your channel id

message = "🚀 New Trade Approved!\n\nSymbol: BTC/USDT\nType: BUY\nEntry: 62,500\nTarget: 64,000\nStoploss: 61,800"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": CHANNEL_ID,
    "text": message,
    "parse_mode": "HTML"  # optional formatting
}

response = requests.post(url, data=payload)
print(response.json())