import pandas as pd
import yfinance as yf

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_xauusd():
    # Načtení dat (GC=F je Gold Futures, nejblíže spotu)
    gold = yf.Ticker("GC=F")
    df_h1 = gold.history(period="1mo", interval="1h")
    df_m15 = gold.history(period="5d", interval="15m")

    if df_h1.empty or df_m15.empty:
        return {"akce": "CHYBA DATA"}

    # --- H1 TREND (EMA 200) ---
    ema200_h1 = df_h1['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
    current_price = df_m15['Close'].iloc[-1]
    trend_h1 = "UP" if current_price > ema200_h1 else "DOWN"

    # --- M15 SIGNÁL (RSI + ATR) ---
    rsi_m15 = calculate_rsi(df_m15['Close']).iloc[-1]
    
    # ATR pro dynamický SL/TP
    high_low = df_m15['High'] - df_m15['Low']
    atr = high_low.rolling(window=14).mean().iloc[-1]

    # Inicializace výstupu pro dashboard
    res = {
        "cena": round(current_price, 1),
        "trend": trend_h1,
        "rsi": round(rsi_m15, 2),
        "akce": "ČEKAT (ŽÁDNÝ VSTUP)",
        "sl": "-",
        "tp": "-"
    }

    # --- STRATEGIE ---
    # LONG: Trend H1 je UP a RSI M15 je pod 35 (přeprodáno)
    if trend_h1 == "UP" and rsi_m15 < 35:
        res["akce"] = "VSTOUPIT DO LONG 🟢"
        res["sl"] = round(current_price - (atr * 3), 1)
        res["tp"] = round(current_price + (atr * 6), 1)

    # SHORT: Trend H1 je DOWN a RSI M15 je nad 65 (překoupeno)
    elif trend_h1 == "DOWN" and rsi_m15 > 65:
        res["akce"] = "VSTOUPIT DO SHORT 🔴"
        res["sl"] = round(current_price + (atr * 3), 2)
        res["tp"] = round(current_price - (atr * 6), 2)

    return res
