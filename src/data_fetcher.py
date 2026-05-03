import yfinance as yf

def fetch_multi_tf(symbol):
    """
    Stáhne data pro více timeframe najednou.
    4h timeframe se dopočítává z 1h dat.
    """

    # Timeframy, které yfinance umí
    timeframes = {
        "5m":  ("5d",  "5m"),
        "30m": ("30d", "30m"),
        "1h":  ("60d", "60m"),
        "1d":  ("1y",  "1d")
    }

    result = {}

    # 1) Stáhneme všechny dostupné TF
    for tf, (period, interval) in timeframes.items():
        try:
            df = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=True,
                multi_level_index=False
            )
            result[tf] = df
        except Exception:
            result[tf] = None

    # 2) Dopočítáme 4h z 1h
    df_1h = result.get("1h")
    if df_1h is not None and not df_1h.empty:
        df_4h = df_1h.resample("4h").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        })
        result["4h"] = df_4h
    else:
        result["4h"] = None

    return result
