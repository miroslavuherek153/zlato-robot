import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# SYMBOLY UPRAVENÉ PRO R STOCKSTRADER (Zlato + Akcie + Krypto ETP)
SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)",
    "NVDA": "🤖 NVIDIA (v ks)",
    "TSLA": "⚡ TESLA (v ks)",
    "BTCE.DE": "₿ BITCOIN ETP (BTCE)",
    "VETH.DE": "⟠ ETHEREUM ETP (VETH)"  # Změněno na stabilnější VETH
}

def vypocitej_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyzuj_a_posli(symbol, nazev):
    # Určení typu aktiva
    is_etp = ".DE" in symbol
    today = datetime.now().weekday()
    
    # O víkendu jsou tyto trhy zavřené
    if today >= 5: return

    data = yf.download(symbol, period="2d", interval="5m", auto_adjust=True, multi_level_index=False)
    if data.empty: return

    current_price = float(data['Close'].iloc[-1])
    vwap = ( ((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume'] ).sum() / data['Volume'].sum()
    rsi = vypocitej_rsi(data['Close']).iloc[-1]

    # RSI Status
    rsi_status = "OK"
    if rsi > 70: rsi_status = "OVER"
    elif rsi < 30: rsi_status = "UNDER"

    # H1 Breakout
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-1]), float(h1['Low'].iloc[-1])
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    
    # Výpočet Vstupu a SL (Buffer 0.1% pro akcie/ETP, 0.40 bodu pro zlato)
    buffer = 0.40 if symbol == "GC=F" else current_price * 0.001
    
    if current_price > vwap:
        vstup, sl = h_high + buffer, h_low
    else:
        vstup, sl = h_low - buffer, h_high

    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5
    
    # Výpočty pro R StocksTrader
    riziko_penize = abs(vstup - sl)
    zisk_penize = abs(tp - vstup)
    trailing_dist = riziko_penize # Doporučená vzdálenost pro Trailing Stop

    # Verdikt
    verdict = "⏳ ČEKEJ"
    if smer == "LONG 🟢" and rsi_status == "UNDER": verdict = "🔥 IDEÁLNÍ SETUP"
    elif smer == "LONG 🟢" and rsi_status == "OK": verdict = "✅ DOBRÝ TREND"
    elif smer == "SHORT 🔴" and rsi_status == "OVER": verdict = "🔥 IDEÁLNÍ SETUP"

    zprava = (
        f"**{nazev}**\n"
        f"Verdikt: **{verdict}** | RSI: `{rsi:.0f}`\n"
        f"Trend: **{smer}** | Cena: `{current_price:.2f}`\n"
        f"--- 💡 PLÁN PRO R STOCKSTRADER ---\n"
        f"🔹 **VSTUP:** `{vstup:.2f}`\n"
        f"🛑 **STOP LOSS:** `{sl:.2f}` (Risk: -{riziko_penize:.2f})\n"
        f"🎯 **TARGET:** `{tp:.2f}` (Zisk: +{zisk_penize:.2f})\n"
        f"🛡️ **TRAILING DIST:** `{trailing_dist:.2f}`\n"
        f"------------------------------"
    )
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try: analyzuj_a_posli(sym, jmeno)
        except: continue
