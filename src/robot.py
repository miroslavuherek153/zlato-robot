import pandas as pd
import pandas_ta as ta
import yfinance as yf

def analyzuj_xauusd():
    # 1. Stažení dat pro zlato (Spot/Futures)
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="1mo", interval="1h")
    df_m15 = gold.history(period="5d", interval="15m")

    if df_h1.empty or df_m15.empty:
        return {"akce": "CHYBA", "duvod": "Data nedostupná"}

    # 2. TREND (H1) - Používáme EMA 200 jako kompas
    df_h1['EMA200'] = ta.ema(df_h1['Close'], length=200)
    posledni_cena_h1 = df_h1['Close'].iloc[-1]
    ema_h1 = df_h1['EMA200'].iloc[-1]
    
    # Pokud je cena nad EMA, jdeme jen LONG. Pod EMA jen SHORT.
    hlavni_trend = "LONG" if posledni_cena_h1 > ema_h1 else "SHORT"

    # 3. SIGNÁL (M15) - RSI a Volatilita (ATR)
    df_m15['RSI'] = ta.rsi(df_m15['Close'], length=14)
    df_m15['ATR'] = ta.atr(df_m15['High'], df_m15['Low'], df_m15['Close'], length=14)
    
    cena = df_m15['Close'].iloc[-1]
    rsi = df_m15['RSI'].iloc[-1]
    atr = df_m15['ATR'].iloc[-1]

    vystup = {
        "akce": "ČEKAT",
        "trend": hlavni_trend,
        "cena": round(cena, 2),
        "sl": 0,
        "tp": 0,
        "duvod": "Trh je v rovnováze"
    }

    # 4. LOGIKA VSTUPU
    # Koupit: Trend je UP + Zlato je "levné" (RSI pod 30)
    if hlavni_trend == "LONG" and rsi < 30:
        vystup["akce"] = "LONG (BUY) 🟢"
        vystup["sl"] = round(cena - (atr * 3.5), 2) # SL 3.5x volatilita
        vystup["tp"] = round(cena + (atr * 7), 2)   # TP s RRR 1:2
        vystup["duvod"] = "Odraz od přeprodané úrovně v rostoucím trendu"

    # Prodat: Trend je DOWN + Zlato je "drahé" (RSI nad 70)
    elif hlavni_trend == "SHORT" and rsi > 70:
        vystup["akce"] = "SHORT (SELL) 🔴"
        vystup["sl"] = round(cena + (atr * 3.5), 2)
        vystup["tp"] = round(cena - (atr * 7), 2)
        vystup["duvod"] = "Odraz od překoupené úrovně v klesajícím trendu"

    return vystup
