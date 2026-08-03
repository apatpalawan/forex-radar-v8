# ==========================================================
# SCORE ENGINE V9.1 PROFESSIONAL
#
# Compatible:
# - Main.py V9.2
# - Signal Engine V9.1
# - Indicator V8.5+
#
# Concept:
# Bot = Filter, Not Decision Maker
#
# Change:
# - Soft EMA scoring
# - No silent score failure
# - Better DW signal filtering
# ==========================================================


import logging

from price_action import detect_price_action
from fibo import get_fibonacci



# ==========================================================
# SAFE VALUE
# ==========================================================

def safe_get(row, key, default=0):

    try:

        value = row.get(
            key,
            default
        )

        if value is None:
            return default

        if str(value) == "nan":
            return default

        return float(value)

    except Exception:
        return default



# ==========================================================
# CALCULATE SCORE
# ==========================================================

def calculate_score(df, trend):

    if df is None or df.empty:
        return 0


    required = [
        "Close",
        "EMA9",
        "EMA21",
        "EMA50"
    ]


    for col in required:

        if col not in df.columns:

            logging.warning(
                f"[SCORE] Missing {col}"
            )

            return 0



    last = df.iloc[-1]


    score = 0
    reasons = []


    # ======================================================
    # MARKET DATA
    # ======================================================

    close = safe_get(
        last,
        "Close"
    )

    ema9 = safe_get(
        last,
        "EMA9"
    )

    ema21 = safe_get(
        last,
        "EMA21"
    )

    ema50 = safe_get(
        last,
        "EMA50"
    )


    # ======================================================
    # EMA TREND (35)
    # ======================================================

    if trend == "BUY":

        if ema9 > ema21 > ema50:

            score += 25

            reasons.append(
                "EMA Bullish"
            )


        if close > ema9:

            score += 10

            reasons.append(
                "Price Above EMA9"
            )


    elif trend == "SELL":

        if ema9 < ema21 < ema50:

            score += 25

            reasons.append(
                "EMA Bearish"
            )


        if close < ema9:

            score += 10

            reasons.append(
                "Price Below EMA9"
            )



    # ======================================================
    # ADX TREND POWER (20)
    # ======================================================

    adx = safe_get(
        last,
        "ADX"
    )


    if adx >= 30:

        score += 20

        reasons.append(
            "ADX Strong"
        )


    elif adx >= 25:

        score += 15

        reasons.append(
            "ADX Trend"
        )


    elif adx >= 20:

        score += 10

        reasons.append(
            "ADX Weak Trend"
        )



    # ======================================================
    # RSI MOMENTUM (15)
    # ======================================================

    rsi = safe_get(
        last,
        "RSI"
    )


    if trend == "BUY":

        if rsi >= 60:

            score += 15

            reasons.append(
                "RSI Bull"
            )


        elif rsi >= 50:

            score += 10

            reasons.append(
                "RSI Positive"
            )


    elif trend == "SELL":

        if rsi <= 40:

            score += 15

            reasons.append(
                "RSI Bear"
            )


        elif rsi <= 50:

            score += 10

            reasons.append(
                "RSI Negative"
            )



    # ======================================================
    # MACD CONFIRMATION (10)
    # ======================================================

    macd = safe_get(
        last,
        "MACD"
    )

    macd_signal = safe_get(
        last,
        "MACD_SIGNAL"
    )


    if trend == "BUY":

        if macd > macd_signal:

            score += 10

            reasons.append(
                "MACD Bull"
            )


    elif trend == "SELL":

        if macd < macd_signal:

            score += 10

            reasons.append(
                "MACD Bear"
            )



    # ======================================================
    # PRICE ACTION (10)
    # ======================================================

    try:

        pa = detect_price_action(
            df
        )

    except Exception:

        pa = {}



    if isinstance(pa, dict):

        if trend == "BUY":

            if (
                pa.get("bullish_engulfing")
                or
                pa.get("hammer")
                or
                pa.get("breakout") == "BUY"
            ):

                score += 10

                reasons.append(
                    "Price Action"
                )


        elif trend == "SELL":

            if (
                pa.get("bearish_engulfing")
                or
                pa.get("shooting_star")
                or
                pa.get("breakout") == "SELL"
            ):

                score += 10

                reasons.append(
                    "Price Action"
                )



    # ======================================================
    # VOLUME (10)
    # ======================================================

    volume = safe_get(
        last,
        "Volume"
    )

    volume_ma = safe_get(
        last,
        "VOL_MA20"
    )


    if volume_ma > 0:

        if volume > volume_ma:

            score += 10

            reasons.append(
                "Volume Spike"
            )



    # ======================================================
    # FIBONACCI (5)
    # ======================================================

    try:

        fibo = get_fibonacci(
            df,
            trend
        )

        if fibo:

            score += 5

            reasons.append(
                "Fibonacci"
            )


    except Exception:

        pass



    # ======================================================
    # FINAL
    # ======================================================

    score = min(
        int(score),
        100
    )


    logging.info(
        f"""
[SCORE DEBUG]

Trend :
{trend}

Close :
{close}

EMA9 :
{ema9}

EMA21 :
{ema21}

EMA50 :
{ema50}

ADX :
{adx}

RSI :
{rsi}

MACD :
{macd}

FINAL SCORE :
{score}

Reason :
{', '.join(reasons)}

"""
    )


    return score
