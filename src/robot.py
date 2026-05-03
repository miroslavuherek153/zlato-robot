import os
from datetime import datetime

from config_loader import load_config
from data_fetcher import fetch_5m
from indicators import rsi, atr
from strategy import determine_direction
from risk import calculate_position_size
from notifier import send_discord
from logger import log_info, log_error
from sentiment import sentiment_score

# ============================
# 🔧 Načtení konfigurace
# ============================
config = load_config()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

RISK_NA_OBCHOD = config["risk_na_obchod"]
TIMEFRAME = config["timeframe"]
PERIOD_DAYS = config["period_days"]

RSI_PERIOD = config["indikatory"]["rsi_period"]
ATR_PERIOD = config["indikatory"]["atr_period"]
ATR_MULT = config["indikatory"]["atr_multiplier"]
RRR = config["indikatory"]["rrr"]

SYMBOLY = config["symboly"]


# ============================
# 🔍 Analýza jednoho symbolu
# ============================
def analyzuj(symbol, nazev):
    log_info(f"Zpracovávám {symbol}...")

    # --- Stažení dat ---
    try:
        data = fetch_5m(symbol)
    except Exception as e:
        log_error(f"Chyba při stahování dat {symbol}: {e}")
        return

    if data.empty:
        log_error(f"Prázdná data pro {symbol}")
        return

    close = data["Close"]
    current_price = float(close.iloc[-1])

    # --- Výpočty indikátorů ---
    vwap = (((data["High"] + data["Low"] + data["Close"]) / 3) * data["Volume"]).sum() / data["Volume"].sum()
    rsi_val = rsi(close, RSI_PERIOD).iloc[-1]
    atr_val = atr(data, ATR_PERIOD).iloc[-1]

    # --- H1 high/low ---
    h1 = data.resample("1h").agg({"High": "max", "Low": "min"})
    if len(h1) < 3:
        log_error(f"Nedostatek H1 dat pro {symbol}")
        return

    h_high = float(h1["High"].iloc[-2])
    h_low = float(h1["Low"].iloc[-2])

    # --- Sentiment ---
    sentiment = sentiment_score(symbol)
    log_info(f"Sentiment {symbol}: {sentiment:.0f}")

    # Filtr: neobchodovat při příliš negativním sentimentu
    if sentiment < 40:
        log_info(f"Sentiment příliš negativní ({sentiment:.0f}), obchod přeskočen.")
        return

    # --- Trend ---
    is_long = determine_direction(current_price, vwap)
    smer = "LONG 🟢" if is_long else "SHORT 🔴"
    barva = 0x2ecc71 if is_long else 0xe74c3c

    # --- Obchodní plán ---
    buffer = atr_val * ATR_MULT
    vstup = h_high if is_long else h_low
    sl = vstup - buffer if is_long else vstup + buffer
    tp = vstup + (vstup - sl) * RRR

    pocet = calculate_position_size(RISK_NA_OBCHOD, vstup, sl)

    # --- TradingView odkaz ---
    clean_symbol = symbol.replace("=F", "")
    chart_url = f"https://www.tradingview.com/symbols/{clean_symbol}"

    # --- Discord embed ---
    payload = {
        "embeds": [{
            "title": nazev,
            "description": f"Aktuální trend je **{smer}**",
            "color": barva,
            "fields": [
                {"name": "RSI", "value": f"`{rsi_val:.0f}`"},
                {"name": "VWAP", "value": f"`{vwap:.2f}`"},
                {"name": "Sentiment", "value": f"`{sentiment:.0f}` / 100"},
                {"name": "Objem", "value": f"`{pocet} ks`"},
                {"name": "Obchodní plán", "value": f"VSTUP `{vstup:.2f}`\nSTOP `{sl:.2f}`\nTARGET `{tp:.2f}`"},
                {"name": "Graf", "value": f"[Otevřít graf]({chart_url})"}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    # --- Odeslání na Discord ---
    if DISCORD_WEBHOOK:
        send_discord(DISCORD_WEBHOOK, payload)

    log_info(f"Hotovo: {symbol}")


# ============================
# ▶️ Hlavní běh
# ============================
if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        analyzuj(sym, jmeno)
