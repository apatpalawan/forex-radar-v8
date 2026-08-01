# ==========================================
# FOREX RADAR V8.7.2
# DATA LOADER PROFESSIONAL
#
# Compatible:
# - Main Engine V8.7.2
# - Signal Engine V8.5
# - Indicator V8.5
#
# FIX:
# - yfinance timeout freeze
# - MultiIndex
# - Forex volume missing
# - Retry system
# ==========================================


import time
import logging
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd


from indicator import add_indicators

from cache_manager import (
    get_cache,
    save_cache
)


from config import (
    PRICE_CACHE_TTL,
    TICKER_MAP,
)



# ==========================================
# DOWNLOAD SETTINGS
# ==========================================

DOWNLOAD_TIMEOUT = 15

MAX_RETRY = 3


# ==========================================================
# DOWNLOAD HELPER
#
# FIX: บาง ticker (พบกับ ^SET50.BK) Yahoo ปฏิเสธ period="max"
# ด้วย error "Period 'max' is invalid, must be one of: 1d, 5d"
# ทั้งที่หน้าเว็บ Yahoo เองแสดงข้อมูลย้อนหลังหลายปีได้ปกติ
#
# นี่คือ known quirk ของ yfinance/Yahoo chart API กับ ticker
# บางตัว (โดยเฉพาะ index ต่างประเทศที่ไม่ใช่ US) ที่ metadata
# "validRanges" ของ ticker ถูกจำกัดไว้ผิดปกติ เวลาเรียกด้วยคำว่า
# "max" แต่ถ้าใช้ start=/end= (วันที่ตรง ๆ) แทนคำว่า period มักจะ
# ข้ามข้อจำกัดนี้ไปได้ เพราะเป็นคนละ endpoint parameter กัน
#
# วิธีแก้: ลอง period="max" ก่อน (เหมือนเดิม) ถ้าโดน error แบบนี้
# หรือได้ข้อมูลว่างเปล่า ให้ไล่ลองด้วย start=/end= แบบช่วงเวลาสั้นลง
# เรื่อย ๆ แทน
# ==========================================================

FALLBACK_LOOKBACK_DAYS = [
    365 * 15,  # ~15 ปี
    365 * 5,   # 5 ปี
    365 * 2,   # 2 ปี
    365,       # 1 ปี
    180,       # 6 เดือน
]


def _download_ohlc(ticker, symbol):
    # ลองแบบเดิมก่อน (period="max") เพราะ ticker ส่วนใหญ่ (หุ้น/
    # ทอง/forex) ใช้วิธีนี้ได้ปกติอยู่แล้ว ไม่อยากเปลี่ยนพฤติกรรม
    # ของสิ่งที่ทำงานดีอยู่แล้ว
    try:
        df = yf.download(
            ticker,
            period="max",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
            timeout=DOWNLOAD_TIMEOUT,
        )

        if df is not None and not df.empty:
            return df

        logging.warning(
            f"{symbol} period=max ได้ข้อมูลว่าง -> ลองใช้ start/end แทน"
        )

    except Exception as e:
        logging.warning(
            f"{symbol} period=max ใช้ไม่ได้ ({e}) -> ลองใช้ start/end แทน"
        )

    # Fallback: ไล่ลองช่วงวันที่แบบชัดเจน (start=/end=) แทนคำว่า "max"
    end_date = datetime.now()

    for days in FALLBACK_LOOKBACK_DAYS:
        start_date = end_date - timedelta(days=days)

        try:
            df = yf.download(
                ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
                timeout=DOWNLOAD_TIMEOUT,
            )

            if df is not None and not df.empty:
                logging.info(
                    f"{symbol} ใช้ start/end ย้อนหลัง {days} วัน ได้ข้อมูล {len(df)} แท่ง"
                )
                return df

        except Exception as e:
            logging.warning(
                f"{symbol} start/end ย้อนหลัง {days} วัน ล้มเหลว: {e}"
            )

    return None


# ==========================================
# DATA LOADER
# ==========================================


def get_data(
        symbol,
        is_stock,
        price_cache
):


    key = (
        f"{symbol}_{is_stock}"
    )



    # ==========================
    # CACHE
    # ==========================

    cache = get_cache(
        price_cache,
        key,
        PRICE_CACHE_TTL
    )


    if cache is not None:

        logging.info(
            f"{symbol} CACHE HIT"
        )

        return cache



    # ==========================
    # SYMBOL MAP
    # ==========================


    if symbol == "^SET50":

        # FIX: ^SET50.BK (ดัชนีดิบ) yfinance ดึงได้แค่ 1 แท่งเท่านั้น
        # ไม่ว่าจะลอง period="max" หรือ start=/end= ยังไงก็ตาม (ยืนยัน
        # แล้วจากการทดสอบจริงหลายรอบ) เพราะ Yahoo ไม่ได้เก็บ intraday
        # tick ย้อนหลังให้ ticker ประเภทนี้ครบเหมือนหุ้น/ETF ทั่วไป
        #
        # ใช้ TDEX.BK (ThaiDEX SET50 ETF) แทน - เป็นกองทุนที่ซื้อขายจริง
        # บนตลาดหลักทรัพย์ ไล่ตามดัชนี SET50 แบบ 1:1 จึงมี Open/High/Low/
        # Close/Volume ปกติสมบูรณ์เหมือนหุ้นทั่วไป ใช้แทนกันได้สำหรับ
        # ดู trend ของตลาด (ราคาต่างกัน แต่ทิศทางเคลื่อนไหวสอดคล้องกัน)
        ticker = "TDEX.BK"


    elif is_stock:

        ticker = (
            f"{symbol}.BK"
        )


    else:

        ticker = TICKER_MAP.get(
            symbol
        )



    if ticker is None:

        logging.warning(
            f"{symbol} NO TICKER MAP"
        )

        return None



    # ==========================
    # DOWNLOAD
    # ==========================


    for attempt in range(
        MAX_RETRY
    ):

        try:

            logging.info(
                f"{symbol} DOWNLOAD {ticker}"
            )



            df = _download_ohlc(
                ticker,
                symbol
            )



            if (
                df is None
                or
                df.empty
            ):

                logging.warning(
                    f"{symbol} EMPTY DATA"
                )

                time.sleep(2)

                continue



            # ==========================
            # FIX YFINANCE MULTI INDEX
            # ==========================


            if isinstance(
                df.columns,
                pd.MultiIndex
            ):

                df.columns = (
                    df.columns
                    .get_level_values(0)
                )



            # ==========================
            # CLEAN COLUMN
            # ==========================


            df.columns = [
                str(c)
                for c in df.columns
            ]



            # FIX (รอบ 2): จากที่ทดสอบจริงพบว่า ^SET50.BK ไม่ได้มีแค่
            # Volume เป็น NaN - แม้แต่ Open/High/Low ก็เป็น NaN ในหลาย
            # แถวด้วย (ดัชนีบางตัวของ Yahoo ไม่มี intraday tick ย้อนหลัง
            # ให้ครบ มีแค่ Close ที่เชื่อถือได้จริง) ทำให้ dropna(subset=
            # OHLC) รอบก่อนยังทิ้งข้อมูลเกือบหมดอยู่ดี
            #
            # แก้โดยเติม Open/High/Low ที่หายไปด้วยค่า Close ของแถวนั้น
            # (ใช้ Close แทนเป็น proxy เวลาไม่มีค่าจริง) ก่อน dropna
            # แล้วเหลือแค่ Close เป็นเงื่อนไขบังคับจริง ๆ อันเดียว
            if "Close" in df.columns:

                for price_col in ("Open", "High", "Low"):

                    if price_col in df.columns:

                        df[price_col] = df[price_col].fillna(
                            df["Close"]
                        )

            # FIX: เดิม dropna() แบบไม่ระบุ subset จะทิ้งแถวที่มี NaN
            # ใน "คอลัมน์ไหนก็ได้" รวมถึง Volume ด้วย - อินเด็กซ์อย่าง
            # ^SET50.BK ไม่มีการซื้อขายจริงจึง Volume เป็น NaN แทบทุกวัน
            # (ไม่ใช่ไม่มีคอลัมน์เลย แค่ค่าว่าง) ทำให้แถวเกือบทั้งหมด
            # ถูกทิ้งไป ตอนนี้เหลือแค่ Close เป็นเงื่อนไขบังคับจริง ๆ
            df = (
                df
                .copy()
                .dropna(
                    subset=[
                        c
                        for c in ("Close",)
                        if c in df.columns
                    ]
                )
            )



            # ==========================
            # REQUIRED PRICE DATA
            # ==========================


            required = [

                "Open",

                "High",

                "Low",

                "Close"

            ]



            missing = [

                c
                for c in required
                if c not in df.columns

            ]



            if missing:

                logging.warning(
                    f"{symbol} Missing {missing}"
                )

                continue



            # ==========================
            # ADD VOLUME IF MISSING
            # Forex ไม่มี Volume จริง
            # ==========================


            if "Volume" not in df.columns:

                df["Volume"] = 0

            else:

                df["Volume"] = df["Volume"].fillna(0)



            # ==========================
            # DATA SIZE CHECK
            # ==========================


            if len(df) < 100:

                logging.warning(
                    f"{symbol} DATA LOW {len(df)}"
                )



            # ==========================
            # INDICATOR ENGINE
            # ==========================


            df = add_indicators(
                df
            )



            if (
                df is None
                or
                df.empty
            ):

                logging.warning(
                    f"{symbol} INDICATOR FAILED"
                )

                continue



            # ==========================
            # REMOVE NAN
            # ==========================


            df = (

                df

                .bfill()

                .ffill()

            )



            # ==========================
            # CACHE SAVE
            # ==========================


            save_cache(

                price_cache,

                key,

                df

            )



            logging.info(

                f"{symbol} DATA OK : {len(df)} candles"

            )


            return df



        except Exception as e:


            logging.error(

                f"{symbol} ERROR "
                f"Attempt {attempt+1}/{MAX_RETRY}: {e}"

            )


            time.sleep(3)



    # ==========================
    # FAIL
    # ==========================


    logging.error(

        f"{symbol} FAILED DOWNLOAD"

    )


    return None