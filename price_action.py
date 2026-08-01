import pandas as pd


# =====================================================
# Safety Check
# =====================================================

def valid_df(df, min_rows=2):

    if df is None:
        return False

    if df.empty:
        return False

    if len(df) < min_rows:
        return False

    required = [
        "Open",
        "High",
        "Low",
        "Close"
    ]

    for col in required:
        if col not in df.columns:
            return False

    return True



# =====================================================
# Bullish Engulfing
# =====================================================

def bullish_engulfing(df):

    if not valid_df(df, 2):
        return False


    prev = df.iloc[-2]
    last = df.iloc[-1]


    return (
        prev["Close"] < prev["Open"]
        and last["Close"] > last["Open"]
        and last["Open"] <= prev["Close"]
        and last["Close"] >= prev["Open"]
    )



# =====================================================
# Bearish Engulfing
# =====================================================

def bearish_engulfing(df):

    if not valid_df(df, 2):
        return False


    prev = df.iloc[-2]
    last = df.iloc[-1]


    return (
        prev["Close"] > prev["Open"]
        and last["Close"] < last["Open"]
        and last["Open"] >= prev["Close"]
        and last["Close"] <= prev["Open"]
    )



# =====================================================
# Hammer
# =====================================================

def hammer(df):

    if not valid_df(df):
        return False


    last = df.iloc[-1]


    body = abs(
        last["Close"] - last["Open"]
    )


    lower = (
        min(last["Close"], last["Open"])
        -
        last["Low"]
    )


    upper = (
        last["High"]
        -
        max(last["Close"], last["Open"])
    )


    if body == 0:
        body = 0.000001


    return (
        lower >= body * 2
        and upper <= body
    )



# =====================================================
# Shooting Star
# =====================================================

def shooting_star(df):

    if not valid_df(df):
        return False


    last = df.iloc[-1]


    body = abs(
        last["Close"] - last["Open"]
    )


    upper = (
        last["High"]
        -
        max(last["Close"], last["Open"])
    )


    lower = (
        min(last["Close"], last["Open"])
        -
        last["Low"]
    )


    if body == 0:
        body = 0.000001


    return (
        upper >= body * 2
        and lower <= body
    )



# =====================================================
# Pin Bar
# =====================================================

def pin_bar(df):

    if not valid_df(df):
        return False


    last = df.iloc[-1]


    body = abs(
        last["Close"]
        -
        last["Open"]
    )


    candle = (
        last["High"]
        -
        last["Low"]
    )


    if candle == 0:
        return False


    return (
        body / candle <= 0.30
    )



# =====================================================
# Inside Bar
# =====================================================

def inside_bar(df):

    if not valid_df(df,2):
        return False


    prev = df.iloc[-2]
    last = df.iloc[-1]


    return (
        last["High"] < prev["High"]
        and
        last["Low"] > prev["Low"]
    )



# =====================================================
# Breakout
# =====================================================

def breakout(df, lookback=20):

    if not valid_df(df, lookback+2):
        return None


    highest = (
        df["High"]
        .rolling(lookback)
        .max()
        .iloc[-2]
    )


    lowest = (
        df["Low"]
        .rolling(lookback)
        .min()
        .iloc[-2]
    )


    close = df.iloc[-1]["Close"]


    if close > highest:
        return "BUY"


    if close < lowest:
        return "SELL"


    return None



# =====================================================
# Price Action Summary
# Compatible Score Engine
# =====================================================

def detect_price_action(df):

    return {

        "bullish_engulfing":
            bullish_engulfing(df),


        "bearish_engulfing":
            bearish_engulfing(df),


        "hammer":
            hammer(df),


        "shooting_star":
            shooting_star(df),


        "pin_bar":
            pin_bar(df),


        "inside_bar":
            inside_bar(df),


        "breakout":
            breakout(df)

    }