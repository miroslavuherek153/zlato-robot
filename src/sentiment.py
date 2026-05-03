import requests
from textblob import TextBlob

def fetch_yahoo_news(symbol):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}"
    try:
        r = requests.get(url, timeout=5).json()
        return r.get("news", [])
    except:
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 až 1
    return (polarity + 1) * 50          # převedeno na 0–100

def sentiment_score(symbol):
    news = fetch_yahoo_news(symbol)
    if not news:
        return 50  # neutrální

    scores = []
    for item in news[:5]:  # vezmeme max 5 článků
        title = item.get("title", "")
        if title:
            scores.append(analyze_sentiment(title))

    if not scores:
        return 50

    return sum(scores) / len(scores)
