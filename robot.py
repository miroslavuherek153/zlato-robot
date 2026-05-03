import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# ============================
# 🔐 Načtení secret proměnných
# ============================
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RISK_NA_OBCHOD = float(os.getenv("RISK_NA_OBCHOD", 50))

# ============================
# 📌 Sledované instrumenty
# ============================
SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)",
    "NVDA": "🤖 NVIDIA (v ks)",
    "TSLA": "⚡ TESLA (v ks)",
    "BITO": "₿ BITCOIN ETF (BITO)",
    "ETHV": "⟠ ETHEREUM ETF (ETHV)"
}

# ============================
# 📈 Indikátory
# ============================
def vypocitej_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def vypocitej_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


# ============================
# 🔍 Analýza + odeslání zprávy
# ============================
def analyzuj_a_posli(symbol, nazev):
    try:
        data = yf.download(
            symbol,
            period="5d",
            interval="5m",
            auto_adjust=True,
            multi_level_index=False
        )
    except Exception as e:
        print(f"Chyba při stahování dat {symbol}: {e}")
        return

    if data.empty:
        print(f"Prázdná data pro {symbol}")
        return

    # --- Výpočty ---
    close = data['Close']
    current_price = float(close.iloc[-1])

    vwap = (((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume']).sum() / data['Volume'].sum()
    rsi = vypocitej_rsi(close).iloc[-1]
    atr = vypocitej_atr(data).iloc[-1]

    # --- H1 high/low ---
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    if len(h1) < 3:
        print(f"Nedostatek H1 dat pro {symbol}")
        return

    h_high = float(h1['High'].iloc[-2])
    h_low = float(h1['Low'].iloc[-2])

    # --- Trend ---
    is_long = current_price > vwap
    smer = "LONG 🟢" if is_long else "SHORT 🔴"
    barva = 0x2ecc71 if is_long else 0xe74c3c

    # --- Obchodní plán ---
    buffer = atr * 1.5
    vstup = h_high if is_long else h_low
    sl = vstup - buffer if is_long else vstup + buffer
    tp = vstup + (vstup - sl) * 2

    risk_na_kus = abs(vstup - sl)
    pocet_kusu = int(RISK_NA_OBCHOD / risk_na_kus) if risk_na_kus > 0 else 0

    # --- Odkaz na graf ---
    clean_symbol = symbol.replace("=F", "")
    chart_url = f"https://www.tradingview.com/symbols/{clean_symbol}"

    # --- Discord embed ---
    payload = {
        "embeds": [{
            "title": nazev,
            "description": f"Aktuální trend je **{smer}**",
            "color": barva,
            "fields": [
                {"name": "📊 Indikátory", "value": f"RSI: `{rsi:.0f}`\nVWAP: `{vwap:.2f}`", "inline": True},
                {"name": "💰 Objem", "value": f"`{pocet_kusu} ks` (Risk {RISK_NA_OBCHOD}$)", "inline": True},
                {"name": "🎯 Obchodní plán", "value": f"**VSTUP:** `{vstup:.2f}`\n**STOP:** `{sl:.2f}`\n**TARGET:** `{tp:.2f}`"},
                {"name": "📈 Graf", "value": f"[Otevřít graf]({chart_url})"}
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Trading Bot | 5m Timeframe"}
        }]
    }

    # --- Odeslání ---
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"Chyba při odesílání na Discord: {e}")


# ============================
# ▶️ Hlavní běh
# ============================
if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        print(f"Zpracovávám {sym}...")
        analyzuj_a_posli(sym, jmeno)
