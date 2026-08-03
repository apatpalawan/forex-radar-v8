# ==========================================================
# SIGNAL ENGINE V9.1 (DEBUG VERSION)
#
# Compatible:
# - Main.py V9.1
# - Score Engine
# - DW Scanner V9.1
#
# Concept:
# Signal Engine = Evaluator
# Debug only - Logic preserved
# ==========================================================


from score import calculate_score
from fibo import get_fibonacci
from price_action import detect_price_action



def analyze_signal(symbol, df):


    if df is None or df.empty:

        print(
            symbol,
            "EMPTY DATA"
        )

        return None



    # ======================================================
    # REQUIRED COLUMN CHECK
    # ======================================================

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
                "MISSING COLUMN:",
                col,
                "AVAILABLE:",
                list(df.columns)
            )

            return None



    last = df.iloc[-1]



    # ======================================================
    # EMA DEBUG
    # ======================================================

    print(

        symbol,

        "CLOSE:",
        round(float(last["Close"]),2),

        "EMA9:",
        round(float(last["EMA9"]),2),

        "EMA21:",
        round(float(last["EMA21"]),2),

        "EMA50:",
        round(float(last["EMA50"]),2)

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

        symbol,

        "TREND RESULT:",

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

        symbol,

        "SCORE:",

        score

    )



    # ======================================================
    # PRICE ACTION / FIBO
    # ======================================================

    price_action = detect_price_action(

        df

    )


    fibo = get_fibonacci(

        df,

        trend

    )



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


    if trend == "SIDEWAY":

        reasons.append(
            "SIDEWAY"
        )


    if last.get("ADX",0) >= 25:

        reasons.append(
            "Strong Trend"
        )


    if (

        trend == "BUY"

        and

        last.get("MACD",0)

        >

        last.get("MACD_SIGNAL",0)

    ):

        reasons.append(
            "MACD Bullish"
        )


    elif (

        trend == "SELL"

        and

        last.get("MACD",0)

        <

        last.get("MACD_SIGNAL",0)

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



    # ======================================================
    # RETURN
    # ======================================================

    return {


        "symbol": symbol,


        "trend": trend,


        "recommendation": recommendation,


        "score": score,


        "price_action": price_action,


        "fibonacci": fibo,


        "volume_spike": volume_spike,


        "trade_ready": score >= 65,


        "reasons": reasons

    }