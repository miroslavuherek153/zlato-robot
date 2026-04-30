import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# SEZNAM AKTIV K SLEDOVÁNÍ (Můžeš si sem přidat další)
SYMBOLY = {
    "GC=F": "🏆 ZLATO (XAUUSD)",
    "NVDA": "🤖 NVIDIA",
    "TSLA": "⚡ TESLA",
    "AAPL": "🍎 APPLE"
}

def analyzuj_a_posli(symbol, nazev):
    # Stažení dat
    data = yf.download(symbol, period="1d", interval="1m", auto_adjust=True, multi_level_index=False)
    
    if data.empty: 
        return

    # Výpočet VWAP
    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (data['TP'] * data['Volume']).sum() / data['Volume'].sum()
    current_price = float(data['Close'].iloc[-1])

    # H1 Breakout (poslední hodina)
    h1_data = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high = float(h1_data['High'].iloc[-1])
    h_low = float(h1_data['Low'].iloc[-1])

    # Logika strategie a výpočet síly trendu
    vzdalenost_od_vwap = abs(((current_price - vwap) / vwap) * 100)
    sila_trendu = "🔥 Silný" if vzdalenost_od_vwap > 0.5 else "💨 Slabý"

    if current_price > vwap:
        smer = "LONG 🟢"
        vstup = h_high * 1.001 if symbol != "GC=F" else h_high + 0.30
        sl = h_low
    else:
        smer = "SHORT 🔴"
        vstup = h_low * 0.999 if symbol != "GC=F" else h_low - 0.30
        sl = h_high
    
    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5

    # Formátování zprávy pro Discord
    zprava = (
        f"**{nazev}**\n"
        f"Směr: {smer} | Trend: {sila_trendu}\n"
        f"Aktuálně: {current_price:.2f} (VWAP: {vwap:.2f})\n"
        f"--- VSTUPNÍ PLÁN ---\n"
        f"🔹 **VSTUP:** {vstup:.2f}\n"
        f"🛑 **STOP LOSS:** {sl:.2f}\n"
        f"🎯 **TAKE PROFIT:** {tp:.2f}\n"
        f"------------------------------"
    )
    
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    # Robot projde všechny symboly v seznamu
    for sym, jmeno in SYMBOLY.items():
        try:
            analyzuj_a_posli(sym, jmeno)
        except Exception as e:
            print(f"Chyba u {sym}: {e}")
