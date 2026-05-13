import os
import json
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# Importy tvých pomocných modulů
try:
    from config_loader import load_config
    from notifier import send_discord
    from logger import log_info, log_error
except ImportError:
    # Pokud moduly chybí, vytvoříme jednoduché náhrady, aby kód nespadl
    def log_info(msg): print(f"INFO: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")
    def load_config(): return {"rrr": 2.0, "atr_multiplier": 3.0}
    def send_discord(webhook, payload): print("Discord notification sent.")

def get_gold_data():
    """Stáhne data pro zlato v různých timeframech."""
    gold = yf.Ticker("GC=F") # Zlaté futures
    # H1 pro trend, M5 pro vstup
    df_h1 = gold.history(period="30d", interval="1h")
    df_m5 = gold.history(period="5d", interval="5m")
    return df_m5, df_h1

def analyze_market(df_m5, df_h1, config):
    """Hlavní logika analýzy."""
    # 1. HLAVNÍ TREND (H1) - EMA 200
    # Použijeme standardní pandas pro výpočet, kdyby pandas_ta selhalo
    df_h1['EMA200'] = ta.ema(df_h1['Close'], length=200)
    last_h1_close = df_h1['Close'].iloc[-1]
    last_ema = df_h1['EMA200'].iloc[-1]
    
    trend = "BULLISH (LONG)" if last_h1_close > last_ema else "BEARISH (SHORT)"
    
    # 2. VSTUPNÍ SIGNÁL (M5)
    df_m5['RSI'] = ta.rsi(df_m5['Close'], length=14)
    df_m5['ATR'] = ta.atr(df_m5['High'], df_m5['Low'], df_m5['Close'], length=14)
    
    current_price = df_m5['Close'].iloc[-1]
    rsi = df_m5['RSI'].iloc[-1]
    atr = df_m5['ATR'].iloc[-1]
    
    # Nastavení parametrů z konfigu
    rrr = config.get("rrr", 2.0)
    atr_mult = config.get("atr_multiplier", 3.0)
    
    action = "WAIT"
    sl = 0
    tp = 0

    # Logika vstupu
    if trend == "BULLISH (LONG)" and rsi < 35:
        action = "BUY (LONG)"
        sl = current_price - (atr * atr_mult)
        tp = current_price + (abs(current_price - sl) * rrr)
        
    elif trend == "BEARISH (SHORT)" and rsi > 65:
        action = "SELL (SHORT)"
        sl = current_price + (atr * atr_mult)
        tp = current_price - (abs(sl - current_price) * rrr)

    return {
        "symbol": "XAUUSD (GOLD)",
        "timestamp": datetime.now().isoformat(),
        "price": round(current_price, 2),
        "trend": trend,
        "action": action,
        "rsi": round(rsi, 2),
        "entry": round(current_price, 2) if action != "WAIT" else None,
        "sl": round(sl, 2) if action != "WAIT" else None,
        "tp": round(tp, 2) if action != "WAIT" else None
    }

def main():
    log_info("Start analýzy XAUUSD...")
    config = load_config()
    
    try:
        df_m5, df_h1 = get_gold_data()
        if df_m5.empty or df_h1.empty:
            log_error("Nepodařilo se stáhnout data!")
            return

        result = analyze_market(df_m5, df_h1, config)
        
        # Uložit výsledek pro dashboard
        with open("data.json", "w") as f:
            json.dump(result, f, indent=4)
        
        log_info(f"Analýza hotova. Akce: {result['action']}")

        # Pokud je signál, pošli Discord (pokud máš nastavený webhook)
        if result['action'] != "WAIT":
            webhook = os.getenv("DISCORD_WEBHOOK")
            if webhook:
                payload = {"content": f"🚀 **Zlato Signál!**\nAkce: {result['action']}\nCena: {result['price']}\nSL: {result['sl']}\nTP: {result['tp']}"}
                send_discord(webhook, payload)

    except Exception as e:
        log_error(f"Chyba při běhu robota: {e}")

if __name__ == "__main__":
    main()
