import os
from datetime import datetime

from data_fetcher import fetch_5m
from indicators import rsi, atr
from strategy import determine_direction
from risk import calculate_position_size
from notifier import send_discord

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
RISK_NA_OBCHOD = float(os.getenv("RISK_NA_OBCHOD", 50))

SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)",
    "NVDA": "🤖 NVIDIA (v ks)",
    "TSLA": "⚡ TESLA (v ks)",
    "BITO": "₿ BITCOIN ETF (BITO)",
    "ETHV": "⟠ ETHEREUM ETF (ETHV)"
}

def analyzuj(symbol, nazev):
    data = fetch_5m(symbol)
    if data.empty:
        print(f"Prázdná data pro {symbol}")
        return

    close = data['Close']
    current_price = float(close.iloc[-1])

    vwap = (((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume']).sum() / data['Volume'].sum()
    rsi_val = rsi(close).iloc[-1]
    atr_val = atr(data).iloc[-1]

    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high = float(h1['High'].iloc[-2])
    h_low = float(h1['Low'].iloc[-2])

    is_long = determine_direction(current_price, vwap)
    smer = "LONG 🟢" if is_long else "SHORT 🔴"
    barva = 0x2ecc71 if is_long else 0xe74c3c

    buffer = atr_val * 1.5
    vstup = h_high if is_long else h_low
    sl = vstup - buffer if is_long else vstup + buffer
    tp = vstup + (vstup - sl) * 2

    pocet = calculate_position_size(RISK_NA_OBCHOD, vstup, sl)

    clean_symbol = symbol.replace("=F", "")
    chart_url = f"https://www.tradingview.com/symbols/{clean_symbol}"

    payload = {
        "embeds": [{
            "title": nazev,
            "description": f"Aktuální trend je **{smer}**",
            "color": barva,
            "fields": [
                {"name": "RSI", "value": f"`{rsi_val:.0f}`"},
                {"name": "VWAP", "value": f"`{vwap:.2f}`"},
                {"name": "Objem", "value": f"`{pocet} ks`"},
                {"name": "Obchodní plán", "value": f"VSTUP `{vstup:.2f}`\nSTOP `{sl:.2f}`\nTARGET `{tp:.2f}`"},
                {"name": "Graf", "value": f"[Otevřít graf]({chart_url})"}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    if DISCORD_WEBHOOK:
        send_discord(DISCORD_WEBHOOK, payload)


if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        analyzuj(sym, jmeno)
