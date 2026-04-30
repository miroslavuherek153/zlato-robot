import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)", "NVDA": "🤖 NVIDIA (v ks)", "TSLA": "⚡ TESLA (v ks)",
    "BTC-USD": "₿ BITCOIN (v ks)", "ETH-USD": "⟠ ETHEREUM (v ks)"
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

    # Logika doporučení
    rsi_status = "OK"
    if rsi > 70: rsi_status = "OVER"
    elif rsi < 30: rsi_status = "UNDER"

    # H1 Breakout
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-1]), float(h1['Low'].iloc[-1])
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    
    # Výpočet Vstupu a SL
    if is_crypto:
        vstup, sl = (h_high * 1.002, h_low) if current_price > vwap else (h_low * 0.998, h_high)
    else:
        vstup, sl = (h_high + 0.40, h_low) if symbol == "GC=F" else (h_high * 1.001, h_low)
        if current_price < vwap:
            vstup, sl = (h_low - 0.40, h_high) if symbol == "GC=F" else (h_low * 0.999, h_high)

    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5
    
    # VÝPOČET PENĚZ (na 1 kus/jednotku)
    riziko_usd = abs(vstup - sl)
    zisk_usd = abs(tp - vstup)

    # CELKOVÝ VERDIKT
    verdict = "⏳ ČEKEJ (Trh hledá směr)"
    if smer == "LONG 🟢" and rsi_status == "UNDER": verdict = "🔥 IDEÁLNÍ SETUP (Kupuj dno)"
    elif smer == "LONG 🟢" and rsi_status == "OK": verdict = "✅ DOBRÝ TREND (Naskoč si)"
    elif smer == "SHORT 🔴" and rsi_status == "OVER": verdict = "🔥 IDEÁLNÍ SETUP (Prodej vrchol)"
    elif rsi_status == "OVER" and smer == "LONG 🟢": verdict = "⚠️ POZOR (Riziko otočení dolů)"

    zprava = (
        f"**{nazev}**\n"
        f"Verdikt: **{verdict}**\n"
        f"RSI: `{rsi:.0f}` | Trend: **{smer}**\n"
        f"--- 📊 PLÁN (na 1 jednotku) ---\n"
        f"🔹 **VSTUP:** `{vstup:.2f}`\n"
        f"🛑 **STOP LOSS:** `{sl:.2f}` (Risk: -{riziko_usd:.2f} $)\n"
        f"🎯 **TARGET:** `{tp:.2f}` (Zisk: +{zisk_usd:.2f} $)\n"
        f"------------------------------"
    )
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try: analyzuj_a_posli(sym, jmeno)
        except: continue
