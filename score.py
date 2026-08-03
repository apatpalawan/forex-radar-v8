import logging

from price_action import detect_price_action
from fibo import get_fibonacci


# ==========================================================
# SCORE ENGINE V9.2 DEBUG PROFESSIONAL
#
# Compatible:
# Main.py V9.2
# Signal Engine V9.1
# Indicator.py V8.5
#
# Concept:
# Debug First - No Hidden Failure
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

    score_detail = {}



    # ======================================================
    # DATA DEBUG
    # ======================================================

    close = safe_get(last,"Close")
    ema9 = safe_get(last,"EMA9")
    ema21 = safe_get(last,"EMA21")
    ema50 = safe_get(last,"EMA50")

    adx = safe_get(last,"ADX")
    rsi = safe_get(last,"RSI")
    macd = safe_get(last,"MACD")
    macd_signal = safe_get(last,"MACD_SIGNAL")

    volume = safe_get(last,"Volume")
    volume_ma = safe_get(last,"VOL_MA20")


    logging.info(
        f"""
INDICATOR DEBUG

Trend : {trend}

Close : {close}

EMA9  : {ema9}
EMA21 : {ema21}
EMA50 : {ema50}

ADX   : {adx}
RSI   : {rsi}

MACD  : {macd}
SIGNAL: {macd_signal}

Volume    : {volume}
VOL MA20  : {volume_ma}
"""
    )



    # ======================================================
    # EMA ALIGNMENT (35)
    # ======================================================

    ema_score = 0


    if trend == "BUY":

        if close > ema9 > ema21 > ema50:

            ema_score = 35

            reasons.append(
                "EMA Bullish"
            )


    elif trend == "SELL":

        if close < ema9 < ema21 < ema50:

            ema_score = 35

            reasons.append(
                "EMA Bearish"
            )


    score += ema_score

    score_detail["EMA"] = ema_score



    # ======================================================
    # ADX TREND POWER (20)
    # ======================================================

    adx_score = 0


    if adx >= 30:

        adx_score = 20

        reasons.append(
            "ADX Strong"
        )


    elif adx >= 25:

        adx_score = 15

        reasons.append(
            "ADX Trend"
        )


    elif adx >= 20:

        adx_score = 10


    score += adx_score

    score_detail["ADX"] = adx_score



    # ======================================================
    # RSI MOMENTUM (15)
    # ======================================================

    rsi_score = 0


    if trend == "BUY":

        if rsi >= 60:

            rsi_score = 15

            reasons.append(
                "RSI Bull"
            )


        elif rsi >= 50:

            rsi_score = 10



    elif trend == "SELL":

        if rsi <= 40:

            rsi_score = 15

            reasons.append(
                "RSI Bear"
            )


        elif rsi <= 50:

            rsi_score = 10



    score += rsi_score

    score_detail["RSI"] = rsi_score



    # ======================================================
    # MACD (10)
    # ======================================================

    macd_score = 0


    if trend == "BUY":

        if macd > macd_signal:

            macd_score = 10

            reasons.append(
                "MACD Bull"
            )


    elif trend == "SELL":

        if macd < macd_signal:

            macd_score = 10

            reasons.append(
                "MACD Bear"
            )


    score += macd_score

    score_detail["MACD"] = macd_score



    # ======================================================
    # PRICE ACTION (10)
    # ======================================================

    pa_score = 0


    try:

        pa = detect_price_action(df)

    except Exception:

        pa = {}



    if trend == "BUY":

        if (
            pa.get("bullish_engulfing")
            or
            pa.get("hammer")
            or
            pa.get("breakout") == "BUY"
        ):

            pa_score = 10

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

            pa_score = 10

            reasons.append(
                "Price Action"
            )


    score += pa_score

    score_detail["PRICE"] = pa_score



    # ======================================================
    # VOLUME (10)
    # ======================================================

    volume_score = 0


    if volume_ma > 0:

        if volume > volume_ma:

            volume_score = 10

            reasons.append(
                "Volume Spike"
            )


    score += volume_score

    score_detail["VOLUME"] = volume_score



    # ======================================================
    # FIBONACCI (5)
    # ======================================================

    fibo_score = 0


    try:

        fibo = get_fibonacci(
            df,
            trend
        )


        if fibo:

            fibo_score = 5

            reasons.append(
                "Fibonacci"
            )


    except Exception:

        pass


    score += fibo_score

    score_detail["FIBO"] = fibo_score



    # ======================================================
    # FINAL
    # ======================================================

    score = min(
        int(score),
        100
    )


    logging.info(
        f"""
========== SCORE DEBUG ==========

Trend : {trend}

Score : {score}/100

DETAIL

EMA    : {score_detail['EMA']}
ADX    : {score_detail['ADX']}
RSI    : {score_detail['RSI']}
MACD   : {score_detail['MACD']}
PRICE  : {score_detail['PRICE']}
VOLUME : {score_detail['VOLUME']}
FIBO   : {score_detail['FIBO']}

REASON

{', '.join(reasons)}

=================================
"""
    )


    return score
