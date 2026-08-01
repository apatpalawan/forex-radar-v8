import logging

from price_action import detect_price_action
from fibo import get_fibonacci


# ==========================================================
# Score Engine V8.5 Professional
# Compatible:
# Main.py V8.4
# Indicator.py V8.5
# Signal Engine V8.5
# DW Scanner V8.4
# ==========================================================


def safe_get(row, key, default=0):

    try:

        value = row.get(key, default)


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
    # EMA ALIGNMENT (35)
    # ======================================================

    close = safe_get(last,"Close")

    ema9 = safe_get(last,"EMA9")

    ema21 = safe_get(last,"EMA21")

    ema50 = safe_get(last,"EMA50")


    if trend == "BUY":

        if close > ema9 > ema21 > ema50:

            score += 35

            reasons.append(
                "EMA Bullish"
            )


    elif trend == "SELL":

        if close < ema9 < ema21 < ema50:

            score += 35

            reasons.append(
                "EMA Bearish"
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



    elif trend == "SELL":

        if rsi <= 40:

            score += 15

            reasons.append(
                "RSI Bear"
            )


        elif rsi <= 50:

            score += 10



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

        pa = detect_price_action(df)


    except Exception:

        pa = {}



    if trend == "BUY":

        if (
            pa.get("bullish_engulfing")
            or pa.get("hammer")
            or pa.get("breakout") == "BUY"
        ):

            score += 10

            reasons.append(
                "Price Action"
            )



    elif trend == "SELL":

        if (
            pa.get("bearish_engulfing")
            or pa.get("shooting_star")
            or pa.get("breakout") == "SELL"
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
        f"[SCORE] {trend} | "
        f"{score}/100 | "
        f"{', '.join(reasons)}"
    )


    return score