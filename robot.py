import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# Načtení tajné adresy pro Discord
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# Částka, kterou jsi ochoten riskovat na JEDEN OBCHOD (v USD)
RISK_NA_OBCHOD = 50 

# SEZNAM SYMBOLŮ
SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)",
    "NVDA": "🤖 NVIDIA (v ks)",
    "TSLA": "⚡ TESLA (v ks)",
    "BITO": "₿ BITCOIN ETF (BITO)",
    "ETHV": "⟠ ETHEREUM ETF (ETHV)"
}

def vypocitej_rsi(series, period=14):
    """Přesné RSI s Wilderovým vyhlazováním (shodné s TradingView)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def vypocitej_atr(data, period=14):
    """Výpočet volatility pro inteligentní Stop-Loss"""
    high_low = data['High'] - data['Low']
    high_close = abs(data['High'] - data['Close'].shift())
    low_close = abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

def analyzuj_a_posli(symbol, nazev):
    # Stažení dat (5m interval, data za poslední 5 dní pro stabilitu indikátorů)
    data = yf.download(symbol, period="5d", interval="5m", auto_adjust=True, multi_level_index=False)
    if data.empty: return

    # Základní hodnoty
    current_price = float(data['Close'].iloc[-1])
    vwap = ( ((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume'] ).sum() / data['Volume'].sum()
    rsi = vypocitej_rsi(data['Close']).iloc[-1]
    atr = vypocitej_atr(data).iloc[-1]

    # RSI Varování
    rsi_alert = ""
    if rsi >= 70: rsi_alert = "\n⚠️ **PŘEKOUPENO!** (Možný obrat dolů)"
    elif rsi <= 30: rsi_alert = "\n⚠️ **PŘEPRODÁNO!** (Možný odraz vzhůru)"

    # Strategie: H1 Breakout + VWAP trend
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-2]), float(h1['Low'].iloc[-2]) # Předchozí uzavřená hodina
    
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    
    # Dynamický Stop-Loss pomocí ATR
    buffer = atr * 1.5
    if current_price > vwap:
        vstup = h_high
        sl = vstup - buffer
        tp = vstup + (vstup - sl) * 2.0 # RRR 1:2
    else:
        vstup = h_low
        sl = vstup + buffer
        tp = vstup - (sl - vstup) * 2.0 # RRR 1:2
    
    riziko_na_kus = abs(vstup - sl)
    pocet_kusu = int(RISK_NA_OBCHOD / riziko_na_kus) if riziko_na_kus > 0 else 0
    
    # --- OPRAVA ODKAZU PRO DISCORD ---
    # Používáme parametr ?symbol=, který Discord bezpečně převede na odkaz
    clean_symbol = symbol.replace("=F", "")
    chart_url = f"https://tradingview.com{clean_symbol}"

    zprava = (
        f"**{nazev}**\n"
        f"Trend: **{smer}** | RSI: `{rsi:.0f}`{rsi_alert}\n"
        f"💰 **OBJEM:** `{pocet_kusu} ks` (risk {RISK_NA_OBCHOD}$)\n"
        f"--- 💡 PLÁN ---\n"
        f"🔹 **VSTUP:** `{vstup:.2f}`\n"
        f"🛑 **STOP:** `{sl:.2f}` (ATR)\n"
        f"🎯 **TARGET:** `{tp:.2f}` (RRR 1:2)\n"
        f"📊 **Graf:** {chart_url}\n"
        f"------------------------------"
    )
    
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})
    else:
        print(zprava)

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try:
            analyzuj_a_posli(sym, jmeno)
        except Exception as e:
            print(f"Chyba u {sym}: {e}")
