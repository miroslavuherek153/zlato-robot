import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# Načtení adresy z trezoru
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def analyzuj_zlato():
    # Přidali jsme auto_adjust a multi_level_index=False - to vyřeší tvou chybu z obrázku
    data = yf.download("GC=F", period="1d", interval="1m", auto_adjust=True, multi_level_index=False)
    
    if data.empty: 
        print("Nepodařilo se stáhnout data.")
        return

    # Výpočet VWAP
    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (data['TP'] * data['Volume']).sum() / data['Volume'].sum()
    current_price = float(data['Close'].iloc[-1])

    # H1 Breakout (poslední hodina)
    h1_data = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high = float(h1_data['High'].iloc[-1])
    h_low = float(h1_data['Low'].iloc[-1])

    # Logika strategie
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    vstup = h_high + 0.30 if current_price > vwap else h_low - 0.30
    sl = h_low if current_price > vwap else h_high
    # RRR 1:1.5
    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5

    zprava = (
        f"**📊 ZLATO (XAUUSD)**\n"
        f"Směr: {smer}\n"
        f"Aktuálně: {current_price:.2f}\n"
        f"VWAP: {vwap:.2f}\n"
        f"-------------------\n"
        f"🔹 **VSTUP:** {vstup:.2f}\n"
        f"🛑 **STOP LOSS:** {sl:.2f}\n"
        f"🎯 **TAKE PROFIT:** {tp:.2f}\n"
        f"-------------------\n"
        f"⏰ Čas signálu: {datetime.now().strftime('%H:%M')}"
    )
    
    # Odeslání na Discord
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})
    print("Signál odeslán na Discord!")

if __name__ == "__main__":
    analyzuj_zlato()
