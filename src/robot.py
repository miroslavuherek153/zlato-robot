import pandas as pd
import pandas_ta as ta
import yfinance as yf

def analyzuj_xauusd():
    """
    Profesionální MTF analýza zlata.
    H1 = Trendový filtr (EMA 200)
    M15 = Vstupní signál (RSI + ATR)
    """
    # 1. Stažení dat (Spotová cena zlata)
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="1mo", interval="1h")
    df_m15 = gold.history(period="5d", interval="15m")

    if df_h1.empty or df_m15.empty:
        return {"akce": "CHYBA DATA", "duvod": "Nepodařilo se stáhnout data"}

    # 2. Analýza trendu na H1 (EMA 200)
    df_h1['EMA200'] = ta.ema(df_h1['Close'], length=200)
    posledni_h1_close = df_h1['Close'].iloc[-1]
    posledni_ema = df_h1['EMA200'].iloc[-1]
    
    # Určení trendu: Cena nad EMA200 = Hledáme jen nákupy (Long)
    trend = "BULLISH (LONG)" if posledni_h1_close > posledni_ema else "BEARISH (SHORT)"

    # 3. Analýza vstupu na M15 (RSI a ATR)
    df_m15['RSI'] = ta.rsi(df_m15['Close'], length=14)
    df_m15['ATR'] = ta.atr(df_m15['High'], df_m15['Low'], df_m15['Close'], length=14)
    
    cena = df_m15['Close'].iloc[-1]
    rsi = df_m15['RSI'].iloc[-1]
    atr = df_m15['ATR'].iloc[-1]

    vystup = {
        "akce": "ČEKAT (Žádný signál)",
        "trend": trend,
        "cena": round(cena, 2),
        "rsi": round(rsi, 1),
        "sl": 0,
        "tp": 0
    }

    # 4. LOGIKA SIGNÁLU
    # LONG: Trend je nahoru + RSI je pod 35 (zlato je lokálně levné)
    if trend == "BULLISH (LONG)" and rsi < 35:
        vystup["akce"] = "LONG (BUY) 🟢"
        vystup["sl"] = round(cena - (atr * 3), 2)  # SL 3x volatilita pod cenu
        vystup["tp"] = round(cena + (atr * 6), 2)  # TP s RRR 1:2
    
    # SHORT: Trend je dolů + RSI je nad 65 (zlato je lokálně drahé)
    elif trend == "BEARISH (SHORT)" and rsi > 65:
        vystup["akce"] = "SHORT (SELL) 🔴"
        vystup["sl"] = round(cena + (atr * 3), 2)
        vystup["tp"] = round(cena - (atr * 6), 2)

    return vystup
