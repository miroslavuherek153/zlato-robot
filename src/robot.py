import pandas as pd
import yfinance as yf
import datetime

def calculate_vwap(df):
    """Výpočet Volume Weighted Average Price (VWAP)."""
    v = df['Volume'].values
    tp = (df['Low'] + df['High'] + df['Close']).values / 3
    return df.assign(VWAP=(tp * v).cumsum() / v.cumsum())

def analyze_xauusd():
    # Sťahujeme dáta pre zlato (XAUUSD)
    gold = yf.Ticker("GC=F")
    # Potrebujeme aspoň 2 dni dát pre korektný VWAP a predchádzajúcu H1 sviečku
    df = gold.history(period="2d", interval="1h")
    
    if len(df) < 2:
        return {"akce": "MÁLO DÁT", "duvod": "Čakám na uzavretie H1 sviečky"}

    df = calculate_vwap(df)
    
    # Údaje z poslednej UZAVRETEJ H1 sviečky
    last_candle = df.iloc[-2]  
    current_price = df.iloc[-1]['Close']
    vwap_val = df.iloc[-1]['VWAP']
    
    # Parametre stratégie z dokumentu 
    spread = 0.30 # ~30 bodov [cite: 8]
    sl_points = 4.5 # Stop Loss 4.5 bodu [cite: 9]
    tp_points = 2.0 # Take Profit 2 body [cite: 9]

    res = {
        "cena": round(current_price, 2),
        "vwap": round(vwap_val, 2),
        "akce": "ČEKAT (ŽÁDNÝ SETUP)",
        "vstup": "-",
        "sl": "-",
        "tp": "-"
    }

    # Kontrola času (stratégia od 07:00 dopoludnia) 
    current_hour = datetime.datetime.now().hour
    if not (7 <= current_hour <= 12):
        res["akce"] = "MIMO OBCHODNÍ ČAS (07-12h)"
        return res

    # 1. SHORT SETUP (Cena pod VWAP) 
    if current_price < vwap_val:
        res["trend"] = "SHORT (Pod VWAP)"
        entry_price = last_candle['Low'] - spread [cite: 8]
        res["akce"] = "SHORT SETUP (Pod Low H1) 🔴"
        res["vstup"] = round(entry_price, 2)
        res["sl"] = round(entry_price + sl_points, 2) [cite: 9]
        res["tp"] = round(entry_price - tp_points, 2) [cite: 9]

    # 2. LONG SETUP (Cena nad VWAP) [cite: 52]
    elif current_price > vwap_val:
        res["trend"] = "LONG (Nad VWAP)"
        entry_price = last_candle['High'] + spread [cite: 52]
        res["akce"] = "LONG SETUP (Nad High H1) 🟢"
        res["vstup"] = round(entry_price, 2)
        res["sl"] = round(entry_price - sl_points, 2)
        res["tp"] = round(entry_price + tp_points, 2)

    return res
