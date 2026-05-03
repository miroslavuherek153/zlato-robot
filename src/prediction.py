import numpy as np
import pandas as pd

def linear_regression_slope(series):
    y = series.values
    x = np.arange(len(y))
    if len(y) < 3:
        return 0
    slope = np.polyfit(x, y, 1)[0]
    return slope

def macd_histogram(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return hist.iloc[-1]

def trend_score(series):
    slope = linear_regression_slope(series[-50:])
    macd = macd_histogram(series)

    score = 50

    if slope > 0:
        score += 20
    else:
        score -= 20

    if macd > 0:
        score += 20
    else:
        score -= 20

    return max(0, min(100, score))

def trend_direction(series):
    score = trend_score(series)
    if score > 60:
        return "UP", score
    if score < 40:
        return "DOWN", score
    return "FLAT", score
