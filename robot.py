import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# Načtení tajné adresy pro Discord
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# Částka, kterou jsi ochoten riskovat na JEDEN OBCHOD (v USD)
RISK_NA_OBCHOD = 50 

# SEZNAM SYMBOLŮ PŘESNĚ PRO TVŮJ ROBOFOREX
SYMBOLY = {
    "GC=F": "🏆 ZLATO (v oz)",
    "NVDA": "🤖 NVIDIA (v ks)",
    "TSLA": "⚡ TESLA (v ks)",
    "BITO": "₿ BITCOIN ETF (BITO)",
    "ETHV": "⟠ ETHEREUM ETF (ETHV)"
}

def vypocitej_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyzuj_a_posli(symbol, nazev):
    # Stažení dat
    data = yf.download(symbol, period="2d", interval="5m", auto_adjust=True, multi_level_index=False)
    if data.empty: return

    current_price = float(data['Close'].iloc[-1])
    vwap = ( ((data['High'] + data['Low'] + data['Close']) / 3) * data['Volume'] ).sum() / data['Volume'].sum()
    rsi = vypocitej_rsi(data['Close']).iloc[-1]

    # H1 Breakout (poslední hodina)
    h1 = data.resample('1h').agg({'High': 'max', 'Low': 'min'})
    h_high, h_low = float(h1['High'].iloc[-1]), float(h1['Low'].iloc[-1])
    smer = "LONG 🟢" if current_price > vwap else "SHORT 🔴"
    
    # Buffer pro vstup (0.40 pro zlato, 0.1% pro akcie)
    buffer = 0.40 if symbol == "GC=F" else current_price * 0.001
    
    if current_price > vwap:
        vstup, sl = h_high + buffer, h_low
    else:
        vstup, sl = h_low - buffer, h_high
    
    tp = vstup + (vstup - sl) * 1.5 if current_price > vwap else vstup - (sl - vstup) * 1.5
    
    # Výpočty peněz a objemu
    riziko_na_kus = abs(vstup - sl)
    pocet_kusu = int(RISK_NA_OBCHOD / riziko_na_kus) if riziko_na_kus > 0 else 0
    
    # Odkaz na graf (TradingView) - OPRAVENO
    tv_symbol = symbol.replace("GC=F", "COMEX:GC1!").replace("ETHV", "AMEX:ETHV").replace("BITO", "NYSE:BITO").replace("NVDA", "NASDAQ:NVDA").replace("TSLA", "NASDAQ:TSLA")
    chart_url = f"https://tradingview.com{tv_symbol}"

    # Sestavení zprávy
    zprava = (
        f"**{nazev}**\n"
        f"Trend: **{smer}** | RSI: `{rsi:.0f}`\n"
        f"💰 **OBJEM:** `{pocet_kusu} ks/oz` (při risku {RISK_NA_OBCHOD}$)\n"
        f"--- 💡 PLÁN ---\n"
        f"🔹 **VSTUP:** `{vstup:.2f}` | 🛑 **STOP:** `{sl:.2f}`\n"
        f"🎯 **TARGET:** `{tp:.2f}` | 🛡️ **TRAILING:** `{riziko_na_kus:.2f}`\n"
        f"🔗 [OTEVŘÍT GRAF]({chart_url})\n"
        f"------------------------------"
    )
    
    requests.post(DISCORD_WEBHOOK_URL, json={"content": zprava})

if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        try:
            analyzuj_a_posli(sym, jmeno)
        except Exception as e:
            print(f"Chyba u {sym}: {e}")
