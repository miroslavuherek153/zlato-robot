import pandas_ta as ta

def proved_technickou_analyzu(df_m15, df_h4):
    """
    Vezme data ze dvou časových rámců a vrátí obchodní doporučení.
    """
    # --- 1. ANALÝZA TRENDU (H4 - 4 hodiny) ---
    # EMA 200 je "svatý grál" trendu. Cena nad ním = trend nahoru.
    df_h4['ema200'] = ta.ema(df_h4['Close'], length=200)
    posledni_cena_h4 = df_h4['Close'].iloc[-1]
    ema_hodnota = df_h4['ema200'].iloc[-1]
    
    trend = "LONG" if posledni_cena_h4 > ema_hodnota else "SHORT"

    # --- 2. ANALÝZA VSTUPU (M15 - 15 minut) ---
    # RSI: pod 30 je zlato levné (přeprodané), nad 70 drahé (překoupené)
    df_m15['rsi'] = ta.rsi(df_m15['Close'], length=14)
    # ATR: měří volatilitu (jak moc se cena hýbe), abychom věděli, kam dát SL
    df_m15['atr'] = ta.atr(df_m15['High'], df_m15['Low'], df_m15['Close'], length=14)
    
    posledni_m15 = df_m15.iloc[-1]
    cena = posledni_m15['Close']
    rsi = posledni_m15['rsi']
    atr = posledni_m15['atr']

    # --- 3. ROZHODNUTÍ O VSTUPU ---
    akce = "ČEKAT (Žádný signál)"
    sl = 0.0
    tp = 0.0

    # Nákup (LONG): Trend je nahoru a cena na M15 trochu klesla (RSI < 40)
    if trend == "LONG" and rsi < 40:
        akce = "KOUPIT (LONG)"
        sl = cena - (atr * 2.5)  # SL dáme kousek pod volatilitu
        tp = cena + (atr * 5.0)  # Cílíme na zisk 1:2 (RRR)

    # Prodej (SHORT): Trend je dolů a cena na M15 trochu stoupla (RSI > 60)
    elif trend == "SHORT" and rsi > 60:
        akce = "PRODAT (SHORT)"
        sl = cena + (atr * 2.5)
        tp = cena - (atr * 5.0)

    return {
        "Symbol": "XAUUSD (Gold)",
        "Trend_H4": trend,
        "Doporuceni": akce,
        "Vstupni_Cena": round(cena, 2),
        "Stop_Loss": round(sl, 2),
        "Take_Profit": round(tp, 2),
        "RSI_M15": round(rsi, 2)
    }
