import pandas as pd
import requests
import time
import urllib.parse
import xml.etree.ElementTree as ET

#TELEGRAM CONFIG
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    max_length = 3500  # safe chunk size

    for i in range(0, len(message), max_length):
        chunk = message[i:i + max_length]

        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": chunk
        })

        print("Telegram response:", response.text)
#  LOAD STOCKS
df = pd.read_csv("ind_nifty100list.csv")
stocks = df[["Company Name","Symbol"]].dropna()

# 🔍 STRONG POSITIVE KEYWORDS
strong_positive = [
    "order", "contract", "deal", "acquisition",
    "joint venture", "partnership", "agreement",
    "profit", "revenue", "growth", "ebitda",
    "strong results", "earnings", "record",
    "secures", "bags", "wins", "expansion",
    "approval", "launch", "capacity"
]

#  NEGATIVE SIGNALS
negative_keywords = [
    "loss", "decline", "fraud", "penalty",
    "downgrade", "fall", "drop", "weak"
]

#  NOISE / NON-TRADEABLE
noise_keywords = [
    "?", "analysis", "survey",
    "shareholding", "disclosure", "open interest",
    "technical", "outlook", "explained",
    "headquarter", "shift"
]

#  FETCH NEWS (RSS)
def fetch_news(query):
    query_encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={query_encoded}+India&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)

        headlines = []
        for item in root.findall(".//item")[:5]:
            title = item.find("title").text.lower()
            headlines.append(title)

        return headlines

    except Exception as e:
        print(f"RSS Error: {e}")
        return []

#  FINAL FILTER (STRICT + CLEAN)
def is_positive(headlines):

    # Reject if any noise
    for h in headlines:
        if any(n in h for n in noise_keywords):
            return False

    #  Reject if negative
    for h in headlines:
        if any(n in h for n in negative_keywords):
            return False

    # Accept if strong trigger exists
    for h in headlines:
        clean_h = h.replace(",", "").replace("%", "").lower()

        if any(p in clean_h for p in strong_positive):
            return True

    return False

#  SCAN
results = []

print(" Scanning stocks...\n")

for i, (_, row) in enumerate(stocks.iterrows()):
    symbol = row["Symbol"]
    name = row["Company Name"]

    print(f"{i+1}/{len(stocks)}: {symbol}")

    try:
        headlines = fetch_news(name)

        ##print("Headlines:", headlines)  # DEBUG

        if len(headlines) == 0:
            continue

        if is_positive(headlines):
            results.append((symbol, headlines[0]))

        time.sleep(0.1)

    except Exception as e:
        print(f"Error with {symbol}: {e}")

# 📤 OUTPUT
if results:
    message = "🟢 Stocks with Positive News Today:\n\n"

    for i, (stock, news) in enumerate(results, start=1):
        message += f"{i}. {stock}\n"
        message += f"   → {news}\n\n"

else:
    message = "🚫 No strong positive triggers today"

send_telegram(message)

print("\nDone ✅")
