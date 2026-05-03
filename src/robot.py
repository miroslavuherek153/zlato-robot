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
from prediction import trend_direction
from exporter import save_json

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

    if sentiment < 40:
        log_info(f"Sentiment příliš negativní ({sentiment:.0f}), obchod přeskočen.")
        return

    # --- Trend Prediction ---
    pred_dir, pred_score = trend_direction(close)
    log_info(f"Predikce {symbol}: {pred_dir} ({pred_score})")

    # Filtr predikce
    if pred_dir == "DOWN" and current_price > vwap:
        log_info("Predikce proti trendu → obchod přeskočen.")
        return
    if pred_dir == "UP" and current_price < vwap:
        log_info("Predikce proti trendu → obchod přeskočen.")
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

    # --- Discord embed (vylepšený) ---
    emoji = "🚀" if pred_dir == "UP" else "📉" if pred_dir == "DOWN" else "⚪"
    sentiment_emoji = "🟢" if sentiment > 60 else "🟡" if sentiment >= 40 else "🔴"

    payload = {
        "embeds": [{
            "title": f"{emoji} {nazev} — {smer}",
            "description": (
                f"**Predikce:** {emoji} `{pred_dir}` (score {pred_score})\n"
                f"**Sentiment:** {sentiment_emoji} `{sentiment:.0f}` / 100\n"
                f"**VWAP:** `{vwap:.2f}`\n"
                f"**RSI:** `{rsi_val:.0f}`\n"
            ),
            "color": barva,
            "fields": [
                {
                    "name": "📊 Obchodní plán",
                    "value": (
                        f"**Vstup:** `{vstup:.2f}`\n"
                        f"**Stop-Loss:** `{sl:.2f}`\n"
                        f"**Take-Profit:** `{tp:.2f}`\n"
                        f"**Objem:** `{pocet} ks`"
                    )
                },
                {
                    "name": "📈 Graf",
                    "value": f"[Otevřít TradingView]({chart_url})"
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    if DISCORD_WEBHOOK:
        send_discord(DISCORD_WEBHOOK, payload)

    # --- JSON export ---
    json_data = {
        "symbol": symbol,
        "nazev": nazev,
        "price": current_price,
        "vwap": vwap,
        "rsi": float(rsi_val),
        "atr": float(atr_val),
        "sentiment": float(sentiment),
        "prediction": pred_dir,
        "prediction_score": pred_score,
        "trend": smer,
        "entry": vstup,
        "stop_loss": sl,
        "take_profit": tp,
        "volume": pocet,
        "timestamp": datetime.utcnow().isoformat()
    }

    save_json(symbol, json_data)

    log_info(f"Hotovo: {symbol}")


# ============================
# ▶️ Hlavní běh
# ============================
if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        analyzuj(sym, jmeno)
