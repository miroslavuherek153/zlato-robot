import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# TVŮJ FINÁLNÍ SEZNAM K SLEDOVÁNÍ
SYMBOLY = {
    "GC=F": "🏆 ZLATO (XAUUSD)",
    "NVDA": "🤖 NVIDIA",
    "TSLA": "⚡ TESLA",
    "AAPL": "🍎 APPLE",
    "BTC-USD": "₿ BITCOIN",
    "ETH-USD": "⟠ ETHEREUM"
}

def analyzuj_a_posli(symbol, nazev):
    # Stažení dat (pro krypto a zlato 2d, aby byl graf plynulý)
    data = yf.download(symbol, period="2d", interval="1m", auto_adjust=True, multi_level_index=False)
    
    if data.empty: return

    # Výpočet VWAP a Aktuální volatility
    data['TP'] = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (data['TP'] * data['Volume']).sum() / data['Volume'].sum()
    current_price = float(data['Close'].iloc[-1])
    
    # Denní změna v procentech
    denni_zmena = ((current_price - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
    volatila_emoji = "🚀" if abs(denni_zmena) > 2 else "⚖️"

    # H1 Breakout
    h1_data = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high = float(h1_data['High'].iloc[-1])
    h_low = float(h1_data['Low'].iloc[-1])

    # Logika směru
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    
    # Nastavení vstupu a SL podle typu aktiva
    if "USD" in symbol: # Krypto
        vstup = h_high * 1.002 if current_price > vwap else h_low * 0.998
        sl = h_low if current_price > vwap else h_high
    elif symbol == "GC=F": # Zlato
        vstup = h_high + 0.40 if current_price > vwap else h_low - 0.40
        sl = h_low if current_price > vwap else h_high
    else: # Akcie
        vstup = h_high * 1.001 if current_price > vwap else h_low * 0.999
        sl = h_low if current_price > vwap else h_high
    
    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5

    # Zpráva pro Discord
    zprava = (
        f"**{nazev}** {volatila_emoji}\n"
        f"Směr: **{smer}** | Dnes: {denni_zmena:+.2f}%\n"
        f"Cena: `{current_price:.2f}` (VWAP: {vwap:.2f})\n"
        f"--- PLÁN ---\n"
        f"🔹 **VSTUP:** {vstup:.2f}\n"
        f"🛑 **STOP:** {sl:.2f}\n"
        f"🎯 **TARGET:** {tp:.2f}"
    )
    
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try:
            analyzuj_a_posli(sym, jmeno)
        except:
            continue
