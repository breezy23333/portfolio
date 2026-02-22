import pandas as pd

def add_indicators(df):
    df["EMA10"] = df["close"].ewm(span=10, adjust=False).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss
    df["RSI14"] = 100 - (100 / (1 + rs))

    return df