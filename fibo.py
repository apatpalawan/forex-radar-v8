import pandas as pd


# =====================================================
# Validation
# =====================================================

def valid_df(df):

    if df is None:
        return False

    if df.empty:
        return False


    required = [
        "High",
        "Low",
        "Close"
    ]


    for col in required:

        if col not in df.columns:
            return False


    return True



# =====================================================
# Fibonacci Levels
# =====================================================

def calculate_fibonacci(df):

    if not valid_df(df):
        return None


    high = df["High"].max()

    low = df["Low"].min()


    diff = high - low


    if diff <= 0:
        return None



    levels = {

        "0.0%": high,

        "23.6%": high - diff * 0.236,

        "38.2%": high - diff * 0.382,

        "50.0%": high - diff * 0.500,

        "61.8%": high - diff * 0.618,

        "100.0%": low,

        "161.8%": high + diff * 0.618

    }


    return levels



# =====================================================
# Nearest Fibonacci Level
# =====================================================

def nearest_fibonacci(df):

    levels = calculate_fibonacci(df)


    if levels is None:
        return "N/A"



    try:

        close = float(
            df.iloc[-1]["Close"]
        )


    except Exception:

        return "N/A"



    nearest = min(
        levels,
        key=lambda x:
        abs(close - levels[x])
    )


    return nearest



# =====================================================
# ATR Safety
# =====================================================

def get_atr(df):

    try:

        atr = float(
            df.iloc[-1]["ATR"]
        )


        if pd.isna(atr):

            return 0


        return atr


    except Exception:

        return 0



# =====================================================
# Trade Plan
# =====================================================

def trade_plan(df, trend):

    levels = calculate_fibonacci(df)


    if levels is None:
        return None



    close = float(
        df.iloc[-1]["Close"]
    )


    atr = get_atr(df)



    # fallback ATR
    if atr <= 0:

        atr = close * 0.01



    if trend == "BUY":


        entry = close


        stop_loss = (
            close -
            (atr * 1.5)
        )


        tp1 = levels["38.2%"]


        tp2 = levels["161.8%"]



    elif trend == "SELL":


        entry = close


        stop_loss = (
            close +
            (atr * 1.5)
        )


        tp1 = levels["61.8%"]


        tp2 = levels["100.0%"]



    else:


        entry = close


        stop_loss = close


        tp1 = levels["50.0%"]


        tp2 = levels["38.2%"]



    return {


        "entry":
            round(entry,2),


        "stop_loss":
            round(stop_loss,2),


        "tp1":
            round(tp1,2),


        "tp2":
            round(tp2,2),


        "nearest":
            nearest_fibonacci(df)

    }



# =====================================================
# Main API
# Signal Engine ใช้ตัวนี้
# =====================================================

def get_fibonacci(df, trend):

    return trade_plan(
        df,
        trend
    )