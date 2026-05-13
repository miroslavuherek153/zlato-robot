import pandas as pd
import yfinance as yf

def calculate_vwap(df):
    v = df['Volume'].values
    tp = (df['Low'] + df['High'] + df['Close']).values / 3
    return df.assign(VWAP=(tp * v).cumsum() / v.cumsum())

def analyze_xauusd():
    gold = yf.Ticker("GC=F")
    df = gold.history(period="2d", interval="1h")
    
    if len(df) < 2:
        return {"akce": "ČEKÁM NA DATA", "vstup": "-", "sl": "-", "tp": "-"}

    df = calculate_vwap(df)
    last_candle = df.iloc[-2]  # Předchozí uzavřená H1 svíce
    current_price = df.iloc[-1]['Close']
    vwap_val = df.iloc[-1]['VWAP']
    
    # Parametry dle strategie [cite: 6, 9]
    spread = 0.30 
    sl_points = 4.5 
    tp_points = 2.0 

    res = {
        "cena": round(current_price, 2),
        "vwap": round(vwap_val, 2),
        "akce": "HLEDÁM SETUP (24/5)",
        "vstup": "-",
        "sl": "-",
        "tp": "-"
    }

    # SHORT SETUP: Cena pod VWAP 
    if current_price < vwap_val:
        entry_price = last_candle['Low'] - spread [cite: 6, 8]
        res["akce"] = "SHORT SETUP (Pod Low H1) 🔴"
        res["vstup"] = round(entry_price, 2)
        res["sl"] = round(entry_price + sl_points, 2) [cite: 6, 9]
        res["tp"] = round(entry_price - tp_points, 2) [cite: 6, 9]

    # LONG SETUP: Cena nad VWAP [cite: 51, 52, 86]
    elif current_price > vwap_val:
        entry_price = last_candle['High'] + spread [cite: 52]
        res["akce"] = "LONG SETUP (Nad High H1) 🟢"
        res["vstup"] = round(entry_price, 2)
        res["sl"] = round(entry_price - sl_points, 2) [cite: 6]
        res["tp"] = round(entry_price + tp_points, 2) [cite: 6]

    return res
