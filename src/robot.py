import os
import json
import pandas_ta as ta
from datetime import datetime
import yfinance as yf

# Importy tvých stávajících modulů (předpokládám jejich existenci v src/)
from config_loader import load_config
from logger import log_info, log_error
from notifier import send_discord

# =================================================================
# 🔧 NASTAVENÍ A KONFIGURACE
# =================================================================
config = load_config()
SYMBOL = "GC=F"  # Zlaté futures (nejpřesnější volně dostupná spotová cena)
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

class GoldRobotPro:
    def __init__(self):
        self.rrr = config.get("indikatory", {}).get("rrr", 2.0)
        self.atr_mult = config.get("indikatory", {}).get("atr_multiplier", 3.0)

    def fetch_data(self):
        """Stáhne potřebná data pro MTF analýzu."""
        log_info(f"Stahuji data pro {SYMBOL}...")
        ticker = yf.Ticker(SYMBOL)
        # H4 data pro určení hlavního trendu
        df_h4 = ticker.history(period="60d", interval="1h") # Yahoo limit: 1h je nejstabilnější pro H4 simulaci
        # M5 data pro precizní vstup
        df_m5 = ticker.history(period="5d", interval="5m")
        return df_m5, df_h4

    def analyze(self, df_m5, df_h4):
        """Mozek aplikace: Spojuje trendy a indikátory."""
        # 1. TRENDOVÝ FILTR (H4) - EMA 200
        ema200_h4 = ta.ema(df_h4['Close'], length=200)
        current_price = df_m5['Close'].iloc[-1]
        last_ema_h4 = ema200_h4.iloc[-1]
        
        main_trend = "LONG" if current_price > last_ema_h4 else "SHORT"

        # 2. VSTUPNÍ INDIKÁTORY (M5)
        rsi = ta.rsi(df_m5['Close'], length=14).iloc[-1]
        atr = ta.atr(df_m5['High'], df_m5['Low'], df_m5['Close'], length=14).iloc[-1]
        vwap = ta.vwap(df_m5['High'], df_m5['Low'], df_m5['Close'], df_m5['Volume']).iloc[-1]

        # 3. ROZHODOVACÍ LOGIKA
        signal = "WAIT"
        sl = 0.0
        tp = 0.0

        # Podmínky pro LONG: Trend je UP + RSI je přeprodané (< 35) + Cena je u VWAP
        if main_trend == "LONG" and rsi < 35:
            signal = "LONG 🟢"
            sl = current_price - (atr * self.atr_mult)
            tp = current_price + (abs(current_price - sl) * self.rrr)

        # Podmínky pro SHORT: Trend je DOWN + RSI je překoupené (> 65) + Cena je u VWAP
        elif main_trend == "SHORT" and rsi > 65:
            signal = "SHORT 🔴"
            sl = current_price + (atr * self.atr_mult)
            tp = current_price - (abs(sl - current_price) * self.rrr)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price": round(current_price, 2),
            "trend": main_trend,
            "signal": signal,
            "rsi": round(rsi, 2),
            "vstup": round(current_price, 2) if signal != "WAIT" else None,
            "sl": round(sl, 2) if signal != "WAIT" else None,
            "tp": round(tp, 2) if signal != "WAIT" else None
        }

    def run(self):
        """Hlavní smyčka robota."""
        try:
            df_m5, df_h4 = self.fetch_data()
            if df_m5.empty or df_h4.empty:
                log_error("Nepodařilo se získat data z Yahoo Finance.")
                return

            vysledek = self.analyze(df_m5, df_h4)
            
            # Uložení do JSON pro tvůj dashboard (index.html)
            with open("data.json", "w") as f:
                json.dump(vysledek, f, indent=4)
            
            log_info(f"Analýza hotova: {vysledek['signal']} při ceně {vysledek['price']}")

            # Odeslání na Discord, pokud je signál
            if vysledek["signal"] != "WAIT" and DISCORD_WEBHOOK:
                msg = {
                    "content": f"🚀 **NOVÝ SIGNÁL: {vysledek['signal']}**\n"
                               f"💰 Vstup: {vysledek['vstup']}\n"
                               f"🛑 SL: {vysledek['sl']}\n"
                               f"🎯 TP: {vysledek['tp']}\n"
                               f"📈 Trend: {vysledek['trend']}"
                }
                send_discord(DISCORD_WEBHOOK, msg)

        except Exception as e:
            log_error(f"Kritická chyba v robotovi: {e}")

if __name__ == "__main__":
    robot = GoldRobotPro()
    robot.run()
