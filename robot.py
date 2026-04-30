import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# Načtení adresy z trezoru
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def analyzuj_zlato():
    data = yf.download("GC=F", period="1d", interval="1m")
    if data.empty: return

    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (data['TP'] * data['Volume']).sum() / data['Volume'].sum()
    current_price = float(data['Close'].iloc[-1])

    # H1 Breakout (poslední hodina)
    h1_data = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1_data['High'].iloc[-1]), float(h1_data['Low'].iloc[-1])

    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    vstup = h_high + 0.30 if current_price > vwap else h_low - 0.30
    sl = h_low if current_price > vwap else h_high
    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5

    zprava = f"**📊 ZLATO (XAUUSD)**\nSměr: {smer}\nAktuálně: {current_price:.2f}\nVWAP: {vwap:.2f}\n---\n🔹 **VSTUP:** {vstup:.2f}\n🛑 **STOP LOSS:** {sl:.2f}\n🎯 **TAKE PROFIT:** {tp:.2f}"
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    analyzuj_zlato()
