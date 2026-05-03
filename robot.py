import os
from datetime import datetime

from config_loader import load_config
from data_fetcher import fetch_multi_tf
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

    # --- Stažení multi-timeframe dat ---
    try:
        data_all = fetch_multi_tf(symbol)
    except Exception as e:
        log_error(f"Chyba při stahování dat {symbol}: {e}")
        return

    data_5m = data_all.get("5m")
    if data_5m is None or data_5m.empty:
        log_error(f"Prázdná 5m data pro {symbol}")
        return

    close_5m = data_5m["Close"]
    current_price = float(close_5m.iloc[-1])

    # --- Výpočty indikátorů pro 5m (hlavní TF) ---
    vwap_5m = (((data_5m["High"] + data_5m["Low"] + data_5m["Close"]) / 3) * data_5m["Volume"]).sum() / data_5m["Volume"].sum()
    rsi_5m = rsi(close_5m, RSI_PERIOD).iloc[-1]
    atr_5m = atr(data_5m, ATR_PERIOD).iloc[-1]

    # --- H1 high/low z 5m dat ---
    h1 = data_5m.resample("1h").agg({"High": "max", "Low": "min"})
    if len(h1) < 3:
        log_error(f"Nedostatek H1 dat pro {symbol}")
        return

    h_high = float(h1["High"].iloc[-2])
    h_low = float(h1["Low"].iloc[-2])

    # --- Sentiment (společný pro všechny TF) ---
    sentiment = sentiment_score(symbol)
    log_info(f"Sentiment {symbol}: {sentiment:.0f}")

    if sentiment < 40:
        log_info(f"Sentiment příliš negativní ({sentiment:.0f}), obchod přeskočen.")
        return

    # --- Trend Prediction (z 5m) ---
    pred_dir, pred_score = trend_direction(close_5m)
    log_info(f"Predikce {symbol}: {pred_dir} ({pred_score})")

    # Filtr predikce (zůstává podle 5m)
    if pred_dir == "DOWN" and current_price > vwap_5m:
        log_info("Predikce proti trendu → obchod přeskočen.")
        return
    if pred_dir == "UP" and current_price < vwap_5m:
        log_info("Predikce proti trendu → obchod přeskočen.")
        return

    # --- Trend (z 5m) ---
    is_long = determine_direction(current_price, vwap_5m)
    smer = "LONG 🟢" if is_long else "SHORT 🔴"
    barva = 0x2ecc71 if is_long else 0xe74c3c

    # --- Obchodní plán (jen z 5m) ---
    buffer = atr_5m * ATR_MULT
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
                f"**VWAP (5m):** `{vwap_5m:.2f}`\n"
                f"**RSI (5m):** `{rsi_5m:.0f}`\n"
            ),
            "color": barva,
            "fields": [
                {
                    "name": "📊 Obchodní plán (5m)",
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

    # ============================
    # 🧠 Multi-timeframe bloky
    # ============================
    tf_blocks = {}

    def build_tf_block(tf_name, df):
        if df is None or df.empty:
            return None
        close = df["Close"]
        price = float(close.iloc[-1])
        vwap = (((df["High"] + df["Low"] + df["Close"]) / 3) * df["Volume"]).sum() / df["Volume"].sum()
        rsi_val = rsi(close, RSI_PERIOD).iloc[-1]
        atr_val = atr(df, ATR_PERIOD).iloc[-1]

        # Predikce a trend pro daný TF (nezávisle)
        tf_pred_dir, tf_pred_score = trend_direction(close)
        tf_is_long = determine_direction(price, vwap)
        tf_smer = "LONG 🟢" if tf_is_long else "SHORT 🔴"

        block = {
            "price": price,
            "vwap": float(vwap),
            "rsi": float(rsi_val),
            "atr": float(atr_val),
            "prediction": tf_pred_dir,
            "prediction_score": tf_pred_score,
            "trend": tf_smer,
        }

        # Obchodní plán necháváme jen pro 5m (varianta A)
        if tf_name == "5m":
            block["entry"] = vstup
            block["stop_loss"] = sl
            block["take_profit"] = tp
            block["volume"] = pocet

        return block

    tf_map = {
        "5m": data_all.get("5m"),
        "30m": data_all.get("30m"),
        "1h": data_all.get("1h"),
        "4h": data_all.get("4h"),
        "1d": data_all.get("1d"),
    }

    for tf_name, df in tf_map.items():
        block = build_tf_block(tf_name, df)
        if block is not None:
            tf_blocks[tf_name] = block

    # --- JSON export (hlavní hodnoty = 5m, plus multi-TF bloky) ---
    json_data = {
        "symbol": symbol,
        "nazev": nazev,
        "price": current_price,
        "vwap": float(vwap_5m),
        "rsi": float(rsi_5m),
        "atr": float(atr_5m),
        "sentiment": float(sentiment),
        "prediction": pred_dir,
        "prediction_score": pred_score,
        "trend": smer,
        "entry": vstup,
        "stop_loss": sl,
        "take_profit": tp,
        "volume": pocet,
        "timestamp": datetime.utcnow().isoformat(),
        "timeframes": tf_blocks
    }

    save_json(symbol, json_data)

    log_info(f"Hotovo: {symbol}")


# ============================
# ▶️ Hlavní běh
# ============================
if __name__ == "__main__":
    for sym, jmeno in SYMBOLY.items():
        analyzuj(sym, jmeno)
