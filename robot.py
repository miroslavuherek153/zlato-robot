import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

SYMBOLY = {
    "GC=F": "🏆 ZLATO", "NVDA": "🤖 NVIDIA", "TSLA": "⚡ TESLA",
    "BTC-USD": "₿ BITCOIN", "ETH-USD": "⟠ ETHEREUM"
}

def vypocitej_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyzuj_a_posli(symbol, nazev):
    is_crypto = "-USD" in symbol
    today = datetime.now().weekday()
    
    if not is_crypto and today >= 5: return

    data = yf.download(symbol, period="2d", interval="5m", auto_adjust=True, multi_level_index=False)
    if data.empty: return

    current_price = float(data['Close'].iloc[-1])
    vwap = ( ((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume'] ).sum() / data['Volume'].sum()
    rsi = vypocitej_rsi(data['Close']).iloc[-1]

    # --- CHYTRÉ DOPORUČENÍ RSI ---
    if rsi > 75:
        rsi_comment = "❌ NEKUPUJ! (Trh je přehřátý, hrozí pád)"
    elif rsi > 60:
        rsi_comment = "⚠️ POZOR (Trh je silný, ale už naskočený)"
    elif rsi < 25:
        rsi_comment = "🚀 SUPER KUP! (Trh je vyprodaný, ideální dno)"
    elif rsi < 40:
        rsi_comment = "✅ DOBRÝ KUP (Cena je nízko, začni sledovat)"
    else:
        rsi_comment = "🆗 STABILNÍ (Trh je v klidu)"

    # H1 Breakout
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-1]), float(h1['Low'].iloc[-1])

    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    
    # Dynamický výpočet vstupu
    if is_crypto:
        vstup, sl = (h_high * 1.002, h_low) if current_price > vwap else (h_low * 0.998, h_high)
    else:
        vstup, sl = (h_high + 0.30, h_low) if symbol == "GC=F" else (h_high * 1.001, h_low)
        if current_price < vwap:
            vstup, sl = (h_low - 0.30, h_high) if symbol == "GC=F" else (h_low * 0.999, h_high)

    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5

    zprava = (
        f"**{nazev}**\n"
        f"📊 RSI: {rsi:.0f} | **{rsi_comment}**\n"
        f"📈 Směr: **{smer}** | Aktuálně: `{current_price:.2f}`\n"
        f"--- 💡 PLÁN --- \n"
        f"🔹 **Vstup (Breakout):** {vstup:.2f}\n"
        f"🛑 **Stop Loss:** {sl:.2f}\n"
        f"🎯 **Target:** {tp:.2f}\n"
        f"------------------------------"
    )
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try: analyzuj_a_posli(sym, jmeno)
        except: continue
