import yfinance as yf

# ============================
# 📥 Multi-timeframe downloader
# ============================

def fetch_multi_tf(symbol):
    """
    Stáhne data pro více timeframe najednou.
    Vrací dict:
    {
        "5m": df,
        "30m": df,
        "1h": df,
        "4h": df,
        "1d": df
    }
    """

    timeframes = {
        "5m":  ("5d",  "5m"),
        "30m": ("30d", "30m"),
        "1h":  ("60d", "60m"),
        "4h":  ("180d", "240m"),   # 4h = 240m
        "1d":  ("1y",  "1d")
    }

    result = {}

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

    return result
