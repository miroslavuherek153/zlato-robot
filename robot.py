import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# Konfigurace
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RISK_NA_OBCHOD = 50 

SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)",
    "NVDA": "🤖 NVIDIA (v ks)",
    "TSLA": "⚡ TESLA (v ks)",
    "BITO": "₿ BITCOIN ETF (BITO)",
    "ETHV": "⟠ ETHEREUM ETF (ETHV)"
}

def vypocitej_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def vypocitej_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = abs(data['High'] - data['Close'].shift())
    low_close = abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

def analyzuj_a_posli(symbol, nazev):
    data = yf.download(symbol, period="5d", interval="5m", auto_adjust=True, multi_level_index=False)
    if data.empty: return

    current_price = float(data['Close'].iloc[-1])
    vwap = ( ((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume'] ).sum() / data['Volume'].sum()
    rsi = vypocitej_rsi(data['Close']).iloc[-1]
    atr = vypocitej_atr(data).iloc[-1]

    # Strategie a barva pruhu
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-2]), float(h1['Low'].iloc[-2])
    
    is_long = current_price > vwap
    smer = "LONG 🟢" if is_long else "SHORT 🔴"
    barva = 0x2ecc71 if is_long else 0xe74c3c  # Zelená vs Červená

    buffer = atr * 1.5
    vstup = h_high if is_long else h_low
    sl = vstup - buffer if is_long else vstup + buffer
    tp = vstup + (vstup - sl) * 2.0
    
    pocet_kusu = int(RISK_NA_OBCHOD / abs(vstup - sl)) if abs(vstup - sl) > 0 else 0
    
    # Odkaz na graf
    clean_symbol = symbol.replace("=F", "")
    chart_url = f"https://tradingview.com{clean_symbol}"

    # Sestavení Embed zprávy pro Discord
    payload = {
        "embeds": [{
            "title": f"{nazev}",
            "description": f"Aktuální trend je **{smer}**",
            "color": barva,
            "fields": [
                {"name": "📊 Indikátory", "value": f"RSI: `{rsi:.0f}`\nVWAP: `{vwap:.2f}`", "inline": True},
                {"name": "💰 Objem", "value": f"`{pocet_kusu} ks` (Risk {RISK_NA_OBCHOD}$)", "inline": True},
                {"name": "🎯 Obchodní plán", "value": f"**VSTUP:** `{vstup:.2f}`\n**STOP:** `{sl:.2f}`\n**TARGET:** `{tp:.2f}`", "inline": False},
                {"name": "📈 Graf", "value": f"[Klikni pro otevření grafu]({chart_url})", "inline": False}
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Trading Bot | 5m Timeframe"}
        }]
    }
    
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try:
            analyzuj_a_posli(sym, jmeno)
        except Exception as e:
            print(f"Chyba u {sym}: {e}")
