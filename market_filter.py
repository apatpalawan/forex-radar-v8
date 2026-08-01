import pandas as pd


# ==========================================
# Market Trend Filter V8.5 Professional
# ==========================================

def get_market_trend(df):

    if df is None or df.empty:
        return "SIDEWAY"

    if len(df) < 200:
        return "SIDEWAY"

    last = df.iloc[-1]

    close = last.get("Close", 0)
    ema9 = last.get("EMA9", 0)
    ema21 = last.get("EMA21", 0)
    ema50 = last.get("EMA50", 0)
    rsi = last.get("RSI", 50)
    adx = last.get("ADX", 0)

    # ==========================================
    # BUY
    # ==========================================

    if (
        close > ema50
        and ema9 > ema21 > ema50
        and rsi >= 55
        and adx >= 25
    ):
        return "BUY"

    # ==========================================
    # SELL
    # ==========================================

    if (
        close < ema50
        and ema9 < ema21 < ema50
        and rsi <= 45
        and adx >= 25
    ):
        return "SELL"

    # ==========================================
    # SIDEWAY
    # ==========================================

    return "SIDEWAY"