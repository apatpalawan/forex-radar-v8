# ==========================================================
# FOREX RADAR V8.7.2
# INDICATOR ENGINE
#
# Compatible:
# - Data Loader V8
# - Signal Engine V8.5
# - Main Engine V8.7.2
#
# Indicators:
# EMA9
# EMA21
# EMA50
# EMA200
# RSI
# MACD
# ADX
# ATR
# Volume MA
# ==========================================================


import pandas as pd
import numpy as np



# ==========================================================
# ADD INDICATORS
# ==========================================================

def add_indicators(df):

    if df is None:
        return None


    if df.empty:
        return None



    # ------------------------------------------------------
    # Copy Safety
    # ------------------------------------------------------

    df = df.copy()



    # ------------------------------------------------------
    # Validate Columns
    # ------------------------------------------------------

    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]


    for col in required:

        if col not in df.columns:
            return None



    close = df["Close"]



    # ======================================================
    # EMA SYSTEM
    # ======================================================

    df["EMA9"] = (
        close
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )


    df["EMA21"] = (
        close
        .ewm(
            span=21,
            adjust=False
        )
        .mean()
    )


    df["EMA50"] = (
        close
        .ewm(
            span=50,
            adjust=False
        )
        .mean()
    )


    df["EMA200"] = (
        close
        .ewm(
            span=200,
            adjust=False
        )
        .mean()
    )



    # ======================================================
    # RSI
    # ======================================================

    delta = close.diff()


    gain = (
        delta
        .clip(lower=0)
    )


    loss = (
        -delta
        .clip(upper=0)
    )


    avg_gain = (
        gain
        .rolling(14)
        .mean()
    )


    avg_loss = (
        loss
        .rolling(14)
        .mean()
    )


    rs = (
        avg_gain /
        avg_loss.replace(
            0,
            np.nan
        )
    )


    df["RSI"] = (
        100 -
        (
            100 /
            (1 + rs)
        )
    )



    # ======================================================
    # MACD
    # ======================================================

    ema12 = (
        close
        .ewm(
            span=12,
            adjust=False
        )
        .mean()
    )


    ema26 = (
        close
        .ewm(
            span=26,
            adjust=False
        )
        .mean()
    )


    df["MACD"] = (
        ema12 -
        ema26
    )


    df["MACD_SIGNAL"] = (
        df["MACD"]
        .ewm(
            span=9,
            adjust=False
        )
        .mean()
    )



    # ======================================================
    # ATR
    # ======================================================

    high_low = (
        df["High"]
        -
        df["Low"]
    )


    high_close = (
        abs(
            df["High"]
            -
            close.shift()
        )
    )


    low_close = (
        abs(
            df["Low"]
            -
            close.shift()
        )
    )


    true_range = pd.concat(
        [
            high_low,
            high_close,
            low_close
        ],
        axis=1
    ).max(axis=1)


    df["ATR"] = (
        true_range
        .rolling(14)
        .mean()
    )



    # ======================================================
    # ADX
    # ======================================================

    up_move = (
        df["High"]
        .diff()
    )


    down_move = (
        -df["Low"]
        .diff()
    )


    plus_dm = np.where(
        (
            up_move > down_move
        )
        &
        (
            up_move > 0
        ),
        up_move,
        0
    )


    minus_dm = np.where(
        (
            down_move > up_move
        )
        &
        (
            down_move > 0
        ),
        down_move,
        0
    )


    tr14 = (
        true_range
        .rolling(14)
        .sum()
    )


    plus_di = (
        100 *
        pd.Series(
            plus_dm,
            index=df.index
        )
        .rolling(14)
        .sum()
        /
        tr14
    )


    minus_di = (
        100 *
        pd.Series(
            minus_dm,
            index=df.index
        )
        .rolling(14)
        .sum()
        /
        tr14
    )


    dx = (
        abs(
            plus_di -
            minus_di
        )
        /
        (
            plus_di +
            minus_di
        )
    ) * 100


    df["ADX"] = (
        dx
        .rolling(14)
        .mean()
    )



    # ======================================================
    # VOLUME
    # ======================================================

    df["VOL_MA20"] = (
        df["Volume"]
        .rolling(20)
        .mean()
    )



    # ======================================================
    # CLEAN
    # ======================================================

    df = (
        df
        .bfill()
        .ffill()
    )


    return df