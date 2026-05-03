import yfinance as yf

def fetch_5m(symbol):
    return yf.download(
        symbol,
        period="5d",
        interval="5m",
        auto_adjust=True,
        multi_level_index=False
    )
