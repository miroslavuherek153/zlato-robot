import pandas as pd
import pandas_ta as ta
import yfinance as yf

def analyzuj_zlato():
    # Stahujeme spotovou cenu (GC=F jsou nejlikvidnější gold futures)
    gold = yf.Ticker("GC=F")
    
    # MULTI-TIMEFRAME: H1 pro trend, M15 pro přesný vstup
    df_h1 = gold.history(period="1mo", interval="1h")
    df_m15 = gold.history(period="5d", interval="15m")

    # 1. TREND (H1) - EMA 200
    df_h1['EMA200'] = ta.ema(df_h1['Close'], length=200)
    trend = "LONG" if df_h1['Close'].iloc[-1] > df_h1['EMA200'].iloc[-1] else "SHORT"

    # 2. SIGNÁL (M15) - RSI a ATR (pro dynamický SL/TP)
    df_m15['RSI'] = ta.rsi(df_m15['Close'], length=14)
    df_m15['ATR'] = ta.atr(df_m15['High'], df_m15['Low'], df_m15['Close'], length=14)
    
    cena = df_m15['Close'].iloc[-1]
    rsi = df_m15['RSI'].iloc[-1]
    atr = df_m15['ATR'].iloc[-1]

    vystup = {"akce": "ČEKAT", "cena": round(cena, 2), "trend": trend}

    # LOGIKA VSTUPU
    if trend == "LONG" and rsi < 30: # Zlato je v trendu, ale momentálně levné
        vystup["akce"] = "LONG (BUY) 🟢"
        vystup["sl"] = round(cena - (atr * 3), 2) # SL 3x volatilita
        vystup["tp"] = round(cena + (atr * 6), 2) # RRR 1:2
    
    elif trend == "SHORT" and rsi > 70: # Zlato padá, ale momentálně je drahé
        vystup["akce"] = "SHORT (SELL) 🔴"
        vystup["sl"] = round(cena + (atr * 3), 2)
        vystup["tp"] = round(cena - (atr * 6), 2)

    return vystup
