import yfinance as yf
import pandas as pd
import requests
import os

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

    # RSI Status
    rsi_status = f"`{rsi:.0f}`"
    if rsi > 70: rsi_status += " 🔥 (PŘEKOUPENO)"
    if rsi < 30: rsi_status += " 🧊 (PŘEPRODÁNO)"

    # Strategie
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-2]), float(h1['Low'].iloc[-2])
    
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    buffer = atr * 1.5
    vstup = h_high if current_price > vwap else h_low
    sl = vstup - buffer if current_price > vwap else vstup + buffer
    tp = vstup + (vstup - sl) * 2.0
    
    riziko_na_kus = abs(vstup - sl)
    pocet_kusu = int(RISK_NA_OBCHOD / riziko_na_kus) if riziko_na_kus > 0 else 0
    
    # --- FORMÁTOVÁNÍ ODKAZU PRO DISCORD ---
    # Používáme [Text](URL), což Discord vždy podbarví a zaktivní
    clean_symbol = symbol.replace("=F", "")
    tv_url = f"https://www.tradingview.com/chart/?symbol={clean_symbol}"
    link_display = f"[OTEVŘÍT GRAF NA TRADINGVIEW]({tv_url})"

    zprava = (
        f"**{nazev}**\n"
        f"Směr: **{smer}** | RSI: {rsi_status}\n"
        f"💰 **OBJEM:** `{pocet_kusu} ks` (risk {RISK_NA_OBCHOD}$)\n"
        f"--- 🎯 PLÁN ---\n"
        f"🔹 **VSTUP:** `{vstup:.2f}`\n"
        f"🛑 **STOP:** `{sl:.2f}`\n"
        f"🎯 **TARGET:** `{tp:.2f}`\n"
        f"📊 **Graf:** {link_display}\n"
        f"------------------------------"
    )
    
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try:
            analyzuj_a_posli(sym, jmeno)
        except Exception as e:
            print(f"Chyba u {sym}: {e}")
