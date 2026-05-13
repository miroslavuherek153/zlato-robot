import pandas as pd
import yfinance as yf

def get_indicators(df):
    # RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA 200 (Exponential Moving Average)
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # ATR (Average True Range) - pro dynamický SL/TP
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df['ATR'] = ranges.max(axis=1).rolling(window=14).mean()
    
    return df

def analyze_xauusd():
    gold = yf.Ticker("GC=F") # Zlaté futures (nejbližší spotu)
    
    # Stáhneme data
    h1_data = gold.history(period="1mo", interval="1h")
    m15_data = gold.history(period="5d", interval="15m")
    
    if h1_data.empty or m15_data.empty:
        return {"error": "Nepodařilo se stáhnout data"}

    h1 = get_indicators(h1_data)
    m15 = get_indicators(m15_data)
    
    current_price = m15['Close'].iloc[-1]
    trend_h1 = "UP" if current_price > h1['EMA200'].iloc[-1] else "DOWN"
    rsi_m15 = m15['RSI'].iloc[-1]
    atr = m15['ATR'].iloc[-1]
    
    output = {
        "cena": round(current_price, 2),
        "trend_h1": trend_h1,
        "rsi": round(rsi_m15, 2),
        "akce": "WAIT",
        "vstup": None,
        "sl": None,
        "tp": None
    }
    
    # STRATEGIE:
    # LONG: Trend na H1 je UP + RSI na M15 je pod 35 (zlato je levné)
    if trend_h1 == "UP" and rsi_m15 < 35:
        output["akce"] = "LONG (BUY) 🟢"
        output["vstup"] = round(current_price, 2)
        output["sl"] = round(current_price - (atr * 3), 2)
        output["tp"] = round(current_price + (atr * 6), 2) # RRR 1:2
        
    # SHORT: Trend na H1 je DOWN + RSI na M15 je nad 65 (zlato je drahé)
    elif trend_h1 == "DOWN" and rsi_m15 > 65:
        output["akce"] = "SHORT (SELL) 🔴"
        output["vstup"] = round(current_price, 2)
        output["sl"] = round(current_price + (atr * 3), 2)
        output["tp"] = round(current_price - (atr * 6), 2)
        
    return output
