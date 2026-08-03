from score import calculate_score
from fibo import get_fibonacci
from price_action import detect_price_action


# ==========================================================
# Signal Engine V9.1 DEBUG PROFESSIONAL
#
# Compatible:
# - Main.py V9.1
# - Indicator V8.5
# - Score Engine
# - DW Scanner
#
# Concept:
# Signal Engine = Evaluator
# Debug first before production tuning
# ==========================================================


def analyze_signal(symbol, df):


    if df is None or df.empty:

        print(
            symbol,
            "EMPTY DATA"
        )

        return None



    required = [

        "Close",
        "EMA9",
        "EMA21",
        "EMA50"

    ]


    for col in required:

        if col not in df.columns:

            print(
                symbol,
                "MISSING COLUMN",
                col
            )

            return None



    last = df.iloc[-1]



    # ======================================================
    # DEBUG MARKET DATA
    # ======================================================

    print(
        "\n========== SIGNAL DEBUG =========="
    )

    print(
        "SYMBOL:",
        symbol
    )

    print(
        "PRICE:",
        round(float(last["Close"]),4)
    )


    print(
        "EMA:",
        {
            "EMA9": round(float(last["EMA9"]),4),
            "EMA21": round(float(last["EMA21"]),4),
            "EMA50": round(float(last["EMA50"]),4)
        }
    )


    print(
        "INDICATORS:",
        {
            "ADX": round(float(last.get("ADX",0)),2),
            "RSI": round(float(last.get("RSI",0)),2),
            "MACD": round(float(last.get("MACD",0)),4),
            "MACD_SIGNAL": round(float(last.get("MACD_SIGNAL",0)),4)
        }
    )



    # ======================================================
    # EMA TREND FILTER
    # ======================================================


    if (

        last["EMA9"] > last["EMA21"]

        and

        last["EMA21"] > last["EMA50"]

        and

        last["Close"] > last["EMA21"]

    ):

        trend = "BUY"



    elif (

        last["EMA9"] < last["EMA21"]

        and

        last["EMA21"] < last["EMA50"]

        and

        last["Close"] < last["EMA21"]

    ):

        trend = "SELL"



    else:

        trend = "SIDEWAY"



    print(
        "TREND:",
        trend
    )



    # ======================================================
    # SCORE ENGINE
    # ======================================================


    score = calculate_score(

        df,

        trend

    )


    print(
        "SCORE:",
        score
    )



    # ======================================================
    # SIDEWAY
    # ======================================================


    if trend == "SIDEWAY":

        print(
            symbol,
            "REJECT : SIDEWAY"
        )

        return None



    # ======================================================
    # SCORE FILTER
    # ======================================================


    if score < 60:

        print(
            symbol,
            "REJECT : SCORE LOW",
            score
        )

        return None




    # ======================================================
    # PRICE ACTION
    # ======================================================


    try:

        price_action = detect_price_action(
            df
        )

    except Exception:

        price_action = {}




    # ======================================================
    # FIBONACCI
    # ======================================================


    try:

        fibo = get_fibonacci(
            df,
            trend
        )

    except Exception:

        fibo = None




    # ======================================================
    # GRADE
    # ======================================================


    if score >= 90:

        grade = "A+"
        confidence = "VERY HIGH"


    elif score >= 80:

        grade = "A"
        confidence = "HIGH"


    elif score >= 70:

        grade = "B"
        confidence = "GOOD"


    elif score >= 60:

        grade = "C"
        confidence = "MEDIUM"


    else:

        grade = "D"
        confidence = "LOW"




    # ======================================================
    # RECOMMENDATION
    # ======================================================


    if trend == "BUY":

        recommendation = "CALL"


    elif trend == "SELL":

        recommendation = "PUT"


    else:

        recommendation = "NEUTRAL"




    # ======================================================
    # REASONS
    # ======================================================


    reasons = []


    if last.get(
        "ADX",
        0
    ) >= 25:

        reasons.append(
            "Strong Trend"
        )



    if (

        trend == "BUY"

        and

        last.get(
            "MACD",
            0
        )

        >

        last.get(
            "MACD_SIGNAL",
            0
        )

    ):

        reasons.append(
            "MACD Bullish"
        )



    elif (

        trend == "SELL"

        and

        last.get(
            "MACD",
            0
        )

        <

        last.get(
            "MACD_SIGNAL",
            0
        )

    ):

        reasons.append(
            "MACD Bearish"
        )



    if fibo:

        reasons.append(
            f"Near Fibo {fibo.get('nearest','-')}"
        )




    # ======================================================
    # VOLUME
    # ======================================================


    try:

        volume_spike = (

            last["Volume"]

            >

            last["VOL_MA20"]

        )


    except:

        volume_spike = False




    print(
        "PASS SIGNAL",
        {
            "trend":trend,
            "score":score,
            "grade":grade,
            "reasons":reasons
        }
    )


    print(
        "=================================\n"
    )




    # ======================================================
    # RETURN
    # ======================================================


    return {


        "symbol": symbol,


        "trend": trend,


        "recommendation": recommendation,


        "score": score,


        "grade": grade,


        "confidence": confidence,


        "price_action": price_action,


        "fibonacci": fibo,


        "volume_spike": volume_spike,


        "reasons": reasons


    }
