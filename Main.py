# ==========================================================
# FOREX RADAR V9 PROFESSIONAL
# MAIN ENGINE
#
# Compatible:
# - BLS API V9.7
# - DW Scanner V9.1 (Filter Only - No Score)
# - DW Formatter V9.0
# - Signal Engine V8.5
#
# Concept:
# "Bot = Filter, Not Decision Maker"
#
# V9 change vs V8.7.2:
# - Removed fake DW "score" and Hybrid Score (Signal 60% + DW 40%).
#   DW Scanner V9.1 no longer returns a "score" field, so the old
#   MIN_DW_SCORE check always evaluated to 0 and silently dropped
#   every single DW signal. That whole scoring layer is gone.
# - Bot no longer picks a "winner" out of the candidates. Every
#   symbol whose signal + DW passed the filter gets sent -
#   ranking/choosing is left to the user.
# ==========================================================

import time
import logging

from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    VERSION,
    STOCKS,
    FOREX,
    SCAN_INTERVAL,
    SEND_TIMES,
)

from data_loader import get_data
from market_filter import get_market_trend
from signal_engine import analyze_signal
from line_notify import send_line
from cache_manager import cleanup_cache
from dw_formatter import format_dw_message
from dw_scanner import get_best_dw


# ==========================================================
# CONFIG
# ==========================================================

# เกณฑ์นี้เป็นของ Signal Engine เดิม (หุ้น/forex BUY-SELL)
# ไม่เกี่ยวกับ DW - อันนี้ยังใช้ระบบเดิมที่ทำงานดีอยู่แล้ว
STOCK_MIN_SCORE = 70
FOREX_MIN_SCORE = 70

DW_SCAN_DELAY = 1.0  # ป้องกัน Rate Limit จาก BLS API (429/403)
DW_CACHE_TIME = 900
COOLDOWN_TIME = 1800  # Cooldown ห้ามแจ้งเตือนซ้ำภายใน 30 นาที (1800 วินาที)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ==========================================================
# MEMORY
# ==========================================================

price_cache = {}
dw_cache = {}
last_alerts = {}     # เก็บเวลาแจ้งเตือนล่าสุดของแต่ละ Symbol เพื่อทำ Cooldown

signal_queue = []
candidate_signals = []

last_send_time = None


# ==========================================================
# TIME & MARKET SCHEDULE
# ==========================================================

def thai_now():
    try:
        return datetime.now(
            ZoneInfo("Asia/Bangkok")
        )
    except Exception:
        return datetime.now()


def is_send_time():
    now = thai_now().strftime("%H:%M")
    return now in SEND_TIMES


def thai_market_open():
    now = thai_now()

    # ตรวจสอบวันหยุดเสาร์ - อาทิตย์
    if now.weekday() >= 5:
        return False

    t = now.time()

    # รอบเช้า: 09:55 - 12:30
    morning = (
        t >= datetime.strptime("09:55", "%H:%M").time()
        and
        t <= datetime.strptime("12:30", "%H:%M").time()
    )

    # รอบบ่าย: 14:25 - 16:40
    afternoon = (
        t >= datetime.strptime("14:25", "%H:%M").time()
        and
        t <= datetime.strptime("16:40", "%H:%M").time()
    )

    return morning or afternoon


# ==========================================================
# RISK SYSTEM
# (ใช้ค่า DW จริง เช่น sensitivity/delta/gearing มาจัดหมวด
#  ไม่ใช่การให้คะแนน/ตัดสินใจแทนผู้ใช้)
# ==========================================================

def get_risk_level(
        sens,
        delta,
        gearing=0,
        is_forex=False
):
    if is_forex:
        return (
            "NORMAL",
            "Swing",
            "Intraday"
        )

    if gearing >= 12 or sens >= 1.25:
        return (
            "HIGH",
            "Scalping",
            "Minutes"
        )

    if (
        sens >= 1.0
        and
        delta >= 0.5
    ):
        return (
            "NORMAL",
            "Momentum",
            "Intraday"
        )

    return (
        "LOW",
        "Trend",
        "Swing"
    )


# ==========================================================
# CANDIDATE
# ==========================================================

def add_candidate(symbol, message):
    candidate_signals.append(
        {
            "symbol": symbol,
            "message": message
        }
    )


# ==========================================================
# LINE SEND
# ==========================================================

def send_queue():
    global last_send_time

    if signal_queue:
        msg = "\n\n".join(
            signal_queue
        )

        ok = send_line(msg)

        if ok:
            logging.info(
                "LINE SENT"
            )
        else:
            logging.error(
                "LINE SEND FAILED (ดูรายละเอียดจาก log ของ line_notify.py ด้านบน)"
            )

        signal_queue.clear()

    else:
        ok = send_line(
            f"""
📊 Forex Radar V{VERSION}

❌ ไม่พบสัญญาณที่ผ่านเงื่อนไข
"""
        )

    last_send_time = (
        thai_now()
        .strftime("%H:%M")
    )

    return ok


# ==========================================================
# MAIN ENGINE
# ==========================================================

def run_scan_cycle(force_send=False):
    """
    สแกน 1 รอบเต็ม (หุ้น/ทอง/forex/DW) แล้วส่ง LINE ถ้าถึงเวลาส่งจริง
    หรือถ้า force_send=True (ใช้ตอนรันครั้งเดียวจบผ่าน GitHub Actions -
    ตัวจับเวลาข้างนอกเป็นคนคุมเวลาแทน ไม่ต้องเช็ค is_send_time() ซ้ำ)

    คืนค่า True เฉพาะเมื่อส่ง LINE ออกไปสำเร็จจริง (ไม่ใช่แค่ "ถึงเวลาส่ง"
    หรือ "พยายามส่ง") - ถ้าไม่มี Token/ส่งไม่สำเร็จ/ไม่ถึงเวลาส่ง จะได้ False
    """
    global last_send_time

    now_time = thai_now().strftime("%H:%M")
    current_timestamp = time.time()

    should_send = (
        force_send
        or
        (
            is_send_time()
            and
            last_send_time != now_time
        )
    )

    # SET50 Symbol Mapping Dictionary
    set50_mapping = {
        "SET50": "SET50",
        "S50": "SET50",
        "S50F": "SET50",
        "^SET50": "SET50"
    }

    # หมายเหตุ: if True / if True ด้านล่างเป็นแค่ตัวคงระดับ indentation เดิม
    # (ของเดิมอยู่ใน while True: / try: 2 ชั้น) ไม่ได้มีผลต่อ logic ใด ๆ
    if True:
        if True:
            # ==================================================
            # SET50 TREND
            # ==================================================

            set50_df = get_data(
                "^SET50",
                True,
                price_cache
            )

            if set50_df is not None:
                market = get_market_trend(
                    set50_df
                )
            else:
                market = "SIDEWAY"

            candidate_signals.clear()

            logging.info(
                f"THAI MARKET OPEN = {thai_market_open()}"
            )

            # ==================================================
            # SCAN SYMBOL
            # ==================================================

            for symbol in (
                ["^SET50"]
                +
                STOCKS
                +
                FOREX
            ):

                is_stock = (
                    symbol in STOCKS
                    or
                    symbol == "^SET50"
                )

                if (
                    is_stock
                    and
                    not thai_market_open()
                ):
                    continue

                # ==================================================
                # LOAD DATA
                # ==================================================

                if symbol == "^SET50":
                    df = set50_df
                else:
                    df = get_data(
                        symbol,
                        is_stock,
                        price_cache
                    )

                if df is None:
                    continue

                # ==================================================
                # ANALYZE SIGNAL
                # ==================================================

                signal = analyze_signal(
                    symbol,
                    df
                )

                if signal is None:
                    continue

                score = signal.get(
                    "score",
                    0
                )

                minimum = (
                    STOCK_MIN_SCORE
                    if is_stock
                    else FOREX_MIN_SCORE
                )

                if score < minimum:
                    continue

                trend = signal.get(
                    "trend",
                    "SIDEWAY"
                )

                # กรองไม่ให้เทรนด์ SIDEWAY เข้ากระบวนการหา DW หรือส่งสัญญาณ
                if trend not in (
                    "BUY",
                    "SELL"
                ):
                    continue

                best_dw = None

                risk = "NORMAL"
                target = "Standard"
                hold = "Intraday"

                # ==================================================
                # DW FILTER PIPELINE (ไม่มี Score - กรองผ่าน/ไม่ผ่านเท่านั้น)
                # ==================================================

                if is_stock:

                    raw_dw_symbol = (
                        "SET50"
                        if symbol == "^SET50"
                        else symbol.replace(".BK", "")
                    )

                    # Mapping SET50 variants safely
                    dw_symbol = set50_mapping.get(raw_dw_symbol, raw_dw_symbol)

                    # แยก Cache Key ตาม Trend และประเภท DW (CALL/PUT) ป้องกันการสลับกัน
                    dw_type_suffix = "CALL" if trend == "BUY" else "PUT"
                    cache_key = f"{dw_symbol}_{trend}_{dw_type_suffix}"

                    dw_list = None

                    # --------------------------
                    # CACHE
                    # --------------------------

                    if cache_key in dw_cache:
                        cache_age = (
                            time.monotonic()
                            -
                            dw_cache[cache_key][0]
                        )

                        if cache_age < DW_CACHE_TIME:
                            dw_list = (
                                dw_cache[cache_key][1]
                            )

                    # --------------------------
                    # LOAD DW
                    # --------------------------

                    if dw_list is None:
                        dw_list = get_best_dw(
                            dw_symbol,
                            trend
                        )

                        if dw_list is None:
                            dw_list = []

                        dw_cache[cache_key] = (
                            time.monotonic(),
                            dw_list
                        )

                        time.sleep(
                            DW_SCAN_DELAY
                        )

                    if not dw_list:
                        logging.info(
                            f"{symbol} NO DW PASS FILTER"
                        )
                        continue

                    # ส่งทุกตัวที่ผ่าน Filter สูงสุด 3 ตัวแรก
                    # (Scanner Sort ตามคุณภาพจริง เช่น Sensitivity/Delta/Gearing/Days ให้แล้ว
                    #  ไม่ใช่การเลือก "ตัวที่ดีที่สุด" แทนผู้ใช้ - แค่จำกัดความยาวข้อความ)
                    best_dw = dw_list[:3]

                    primary_dw = best_dw[0]

                    sens = float(
                        primary_dw.get(
                            "sensitivity"
                        )
                        or 0
                    )

                    # รองรับทั้ง abs_delta และ delta ปกติ (แก้ปัญหา PUT Delta ติดลบ)
                    delta = float(
                        primary_dw.get(
                            "abs_delta",
                            primary_dw.get(
                                "delta",
                                0
                            )
                        )
                    )

                    gearing = float(
                        primary_dw.get(
                            "effective_gearing",
                            0
                        )
                    )

                    risk, target, hold = get_risk_level(
                        sens,
                        delta,
                        gearing
                    )

                    logging.info(
                        f"""
DW FOUND
Symbol   : {symbol}
Trend    : {trend}
Signal   : {score}
DW Count : {len(best_dw)}
Top DW   : {primary_dw.get('symbol')}
Sens     : {sens}
Delta    : {delta}
Gearing  : {gearing}
"""
                    )

                # ==================================================
                # FOREX
                # ==================================================

                else:
                    best_dw = "FOREX"

                    risk, target, hold = get_risk_level(
                        0,
                        0,
                        0,
                        True
                    )

                # ==================================================
                # COOLDOWN ALERT CHECK
                # ==================================================

                alert_key = f"{symbol}_{trend}_{primary_dw.get('symbol') if is_stock else 'FOREX'}"
                if alert_key in last_alerts:
                    if current_timestamp - last_alerts[alert_key] < COOLDOWN_TIME:
                        logging.info(f"{symbol} SKIPPED DUE TO COOLDOWN")
                        continue

                # บันทึกเวลาที่แจ้งเตือนล่าสุด
                last_alerts[alert_key] = current_timestamp

                # ==================================================
                # FORMAT MESSAGE
                # ==================================================

                message = format_dw_message(
                    trend=trend,
                    symbol=(
                        "SET50"
                        if symbol == "^SET50"
                        else symbol
                    ),
                    dw=best_dw,
                    market=market,
                    price_action=
                    signal.get(
                        "price_action"
                    ),
                    fibo=
                    signal.get(
                        "fibonacci"
                    ),
                    risk=risk,
                    target=target,
                    hold=hold
                )

                add_candidate(
                    symbol,
                    message
                )

            # ==================================================
            # BUILD QUEUE
            # ไม่มีการจัดอันดับ/เลือกตัวเด็ดแทนผู้ใช้อีกต่อไป
            # ส่งทุกสัญญาณที่ผ่าน Filter ในรอบสแกนนี้
            # ==================================================

            signal_queue.clear()

            for item in candidate_signals:
                signal_queue.append(
                    item["message"]
                )

            # ==================================================
            # SEND (ถึงเวลาจริง หรือถูกบังคับด้วย force_send)
            # ==================================================

            send_success = False

            if should_send:
                send_success = send_queue()

            # ==================================================
            # CLEAN MEMORY
            # ==================================================

            cleanup_cache(
                price_cache,
                dw_cache,
                last_alerts
            )

    return send_success


# ==========================================================
# CONTINUOUS MODE
# รันตลอดในเครื่อง/เซิร์ฟเวอร์ที่เปิดค้างได้ (ไม่เหมาะกับ GitHub Actions)
# สำหรับ GitHub Actions ให้ใช้ run_once.py แทน
# ==========================================================

def main():
    logging.info(
        f"Forex Radar V{VERSION} START"
    )

    while True:
        try:
            run_scan_cycle()

            time.sleep(
                SCAN_INTERVAL
            )

        except Exception as e:
            logging.exception(
                f"ERROR {e}"
            )
            time.sleep(60)


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":
    main()
