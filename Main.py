# ==========================================================
# FOREX RADAR V9.3 PROFESSIONAL
# MAIN ENGINE
#
# Concept:
# Bot = Filter, Not Decision Maker
#
# Improvements:
# - Full Debug Pipeline
# - Track rejection reason
# - Signal / Score / Trend separated
# - No silent failure
# - Ready for DW Filter Engine
# - V9.3: เพิ่ม Volume Anomaly Scanner (หุ้นไทย) แยกอิสระจาก
#   ระบบ EMA Trend/Score เดิม - เจอ Volume ผิดปกติ -> หา DW
#   ที่ sensitivity ใกล้ 1 หรือมากกว่าให้ทันที
# ==========================================================

import time
import logging

from datetime import datetime
from zoneinfo import ZoneInfo

from config import (
    VERSION,
    STOCKS,
    SCAN_INTERVAL,
    SEND_TIMES,
    DW_FALLBACK_SENSITIVITY,
)

from data_loader import get_data
from market_filter import get_market_trend
from signal_engine import analyze_signal
from line_notify import send_line
from cache_manager import cleanup_cache
from dw_formatter import format_dw_message
from dw_scanner import get_best_dw
from volume_scanner import detect_abnormal_volume

# ==========================================================
# CONFIG
# ==========================================================
# ปรับลดค่า Min Score ชั่วคราวเพื่อตรวจสอบ Pipeline ช่วง Debug
STOCK_MIN_SCORE = 40
FOREX_MIN_SCORE = 40

DW_SCAN_DELAY = 1.0
DW_CACHE_TIME = 900
COOLDOWN_TIME = 1800

# Volume Anomaly Scanner: sensitivity ที่อยากได้ก่อน (ใกล้ 1 หรือเกิน)
VOLUME_ALERT_MIN_SENSITIVITY = 1.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ==========================================================
# MEMORY
# ==========================================================
price_cache = {}
dw_cache = {}
last_alerts = {}
signal_queue = []
candidate_signals = []
last_send_time = None

# ==========================================================
# DEBUG SYSTEM V9.2
# Track every pipeline stage
# ==========================================================
scan_debug = {
    "scan_count": 0,
    "data_pass": 0,
    "signal_found": 0,
    "score_pass": 0,
    "trend_pass": 0,
    "dw_pass": 0,
    "dw_fail": 0,
    "volume_alert": 0,
    "reject": {
        "no_data": 0,
        "signal_none": 0,
        "score_low": 0,
        "sideway": 0,
        "dw_fail": 0,
        "error": 0
    },
    "symbols": [],
    "data_symbols": []
}


def reset_debug():
    global scan_debug
    scan_debug = {
        "scan_count": 0,
        "data_pass": 0,
        "signal_found": 0,
        "score_pass": 0,
        "trend_pass": 0,
        "dw_pass": 0,
        "dw_fail": 0,
        "volume_alert": 0,
        "reject": {
            "no_data": 0,
            "signal_none": 0,
            "score_low": 0,
            "sideway": 0,
            "dw_fail": 0,
            "error": 0
        },
        "symbols": [],
        "data_symbols": []
    }


def debug_report():
    if scan_debug["signal_found"] > 0 or scan_debug["volume_alert"] > 0:
        result = "SIGNAL FOUND"
    else:
        result = "NO SIGNAL"

    return f"""
📊 Forex Radar V{VERSION}
SCAN REPORT
Symbol Scan : {scan_debug['scan_count']}
Data OK : {scan_debug['data_pass']}
Signal : {scan_debug['signal_found']}
Score Pass : {scan_debug['score_pass']}
Trend Pass : {scan_debug['trend_pass']}
DW Pass : {scan_debug['dw_pass']}
DW Fail : {scan_debug['dw_fail']}
Volume Alert : {scan_debug['volume_alert']}

REJECT REASON
No Data : {scan_debug['reject']['no_data']}
No Signal : {scan_debug['reject']['signal_none']}
Score Low : {scan_debug['reject']['score_low']}
Sideway : {scan_debug['reject']['sideway']}
DW Fail : {scan_debug['reject']['dw_fail']}
Error : {scan_debug['reject']['error']}

Result:{result}
"""

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

    if now.weekday() >= 5:
        return False

    t = now.time()

    morning = (
        t >= datetime.strptime("09:55", "%H:%M").time()
        and
        t <= datetime.strptime("12:30", "%H:%M").time()
    )

    afternoon = (
        t >= datetime.strptime("14:25", "%H:%M").time()
        and
        t <= datetime.strptime("16:40", "%H:%M").time()
    )

    return morning or afternoon

# ==========================================================
# RISK SYSTEM
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
# CANDIDATE MANAGEMENT
# ==========================================================
def add_candidate(symbol, message):
    candidate_signals.append(
        {
            "symbol": symbol,
            "message": message
        }
    )

# ==========================================================
# LINE SEND SYSTEM
# ==========================================================
def send_queue():
    global last_send_time

    if signal_queue:
        # FIX: ส่ง list ของแต่ละ signal message ตรง ๆ แทนที่จะ
        # join รวมเป็นก้อนเดียวก่อน - ให้ send_line() เป็นคนแบ่ง
        # เป็นหลาย message ตามความยาว UTF-16 จริงแทน (กันปัญหา
        # โดน LINE ตอบ 400 "Length must be between 0 and 5000"
        # ตอนมีหลาย signal พร้อมกันจนข้อความรวมยาวเกิน)
        ok = send_line(list(signal_queue))

        if ok:
            logging.info(
                "LINE SENT"
            )
        else:
            logging.error(
                "LINE SEND FAILED"
            )

        signal_queue.clear()
    else:
        ok = send_line(
            debug_report()
        )

    last_send_time = (
        thai_now()
        .strftime("%H:%M")
    )

    return ok

# ==========================================================
# DW SYMBOL MAPPING
# ==========================================================
SET50_MAPPING = {
    "SET50": "SET50",
    "S50": "SET50",
    "S50F": "SET50",
    "^SET50": "SET50"
}


def _dw_symbol_for(symbol):
    raw_dw_symbol = (
        "SET50"
        if symbol == "^SET50"
        else symbol.replace(".BK", "")
    )
    return SET50_MAPPING.get(
        raw_dw_symbol,
        raw_dw_symbol
    )

# ==========================================================
# MAIN SCAN ENGINE V9.3
# ==========================================================
def run_scan_cycle(force_send=False):
    global last_send_time

    reset_debug()

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

    for symbol in (
        ["^SET50"]
        +
        STOCKS
    ):
        scan_debug["scan_count"] += 1
        scan_debug["symbols"].append(
            symbol
        )

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

        if symbol == "^SET50":
            df = set50_df
        else:
            df = get_data(
                symbol,
                is_stock,
                price_cache
            )

        # FIX: หน่วงเวลาสั้น ๆ ระหว่าง symbol ที่ดึงจริง (ไม่โดน cache)
        # เพื่อไม่ให้ยิง request หา Yahoo รัวเกินไปทั้งรอบสแกน
        # ซึ่งเป็นสาเหตุหลักที่ทำให้โดน rate-limit/บล็อกจน "Data OK: 0"
        time.sleep(1)

        if df is None:
            scan_debug["reject"]["no_data"] += 1
            logging.info(
                f"{symbol} REJECT : NO DATA"
            )
            continue

        scan_debug["data_pass"] += 1
        scan_debug["data_symbols"].append(
            symbol
        )

        logging.info(
            f"""
DATA DEBUG
Symbol : {symbol}
Close : {df.iloc[-1].get('Close')}
EMA9 : {df.iloc[-1].get('EMA9')}
EMA21 : {df.iloc[-1].get('EMA21')}
EMA50 : {df.iloc[-1].get('EMA50')}
"""
        )

        # ==================================================
        # VOLUME ANOMALY SCAN (เฉพาะหุ้นไทยใน STOCKS)
        #
        # แยกอิสระจากระบบ Trend/Score EMA เดิมด้านล่าง - รันคู่กัน
        # ไปทุกรอบโดยไม่ขึ้นกับผลของ analyze_signal() เลย ถ้าเจอ
        # Volume ผิดปกติ จะหา DW ที่ sensitivity ใกล้ 1 หรือมากกว่า
        # ให้ทันที (ผ่อนเป็น DW_FALLBACK_SENSITIVITY ถ้าหาไม่เจอ)
        # ==================================================
        if symbol in STOCKS:
            try:
                vol_hit = detect_abnormal_volume(symbol, df)
            except Exception as e:
                vol_hit = None
                logging.exception(
                    f"{symbol} VOLUME SCAN ERROR {e}"
                )

            if vol_hit:
                vol_alert_key = (
                    f"VOL_{symbol}_{vol_hit['direction']}"
                )

                on_cooldown = (
                    vol_alert_key in last_alerts
                    and
                    (
                        current_timestamp
                        -
                        last_alerts[vol_alert_key]
                    )
                    <
                    COOLDOWN_TIME
                )

                if on_cooldown:
                    logging.info(
                        f"{symbol} VOLUME ALERT COOLDOWN"
                    )
                else:
                    dw_symbol = _dw_symbol_for(symbol)

                    vol_dw_list = get_best_dw(
                        dw_symbol,
                        vol_hit["direction"],
                        min_sensitivity=VOLUME_ALERT_MIN_SENSITIVITY
                    )

                    if not vol_dw_list:
                        # ไม่เจอ DW sensitivity >= 1 พอดี -> ผ่อนเกณฑ์
                        # ลงมาที่ DW_FALLBACK_SENSITIVITY (ใกล้ 1 แทน)
                        logging.info(
                            f"{symbol} VOLUME ALERT : NO DW >= "
                            f"{VOLUME_ALERT_MIN_SENSITIVITY}, "
                            f"ลองผ่อนเป็น {DW_FALLBACK_SENSITIVITY}"
                        )
                        vol_dw_list = get_best_dw(
                            dw_symbol,
                            vol_hit["direction"],
                            min_sensitivity=DW_FALLBACK_SENSITIVITY
                        )

                    if vol_dw_list:
                        last_alerts[vol_alert_key] = current_timestamp
                        scan_debug["volume_alert"] += 1

                        vol_message = format_dw_message(
                            trend=vol_hit["direction"],
                            symbol=symbol,
                            dw=vol_dw_list[:3],
                            market=market,
                            reasons=[
                                f"Volume ผิดปกติ x{vol_hit['ratio']:.1f} "
                                f"เท่าของค่าเฉลี่ย 20 วัน"
                            ],
                            risk="HIGH",
                            target="Momentum",
                            hold="Intraday",
                        )

                        add_candidate(
                            f"VOL_{symbol}",
                            vol_message
                        )

                        logging.info(
                            f"{symbol} VOLUME ALERT SENT : "
                            f"x{vol_hit['ratio']:.2f} "
                            f"DIR={vol_hit['direction']} "
                            f"DW={vol_dw_list[0].get('symbol')} "
                            f"Sens={vol_dw_list[0].get('sensitivity')}"
                        )
                    else:
                        logging.info(
                            f"{symbol} VOLUME ALERT : NO DW PASSED "
                            f"(แม้ผ่อนเกณฑ์แล้ว)"
                        )

        try:
            signal = analyze_signal(
                symbol,
                df
            )
        except Exception as e:
            scan_debug["reject"]["error"] += 1
            logging.exception(
                f"{symbol} SIGNAL ERROR {e}"
            )
            continue

        if signal is None:
            scan_debug["reject"]["signal_none"] += 1
            logging.info(
                f"{symbol} REJECT : NO SIGNAL"
            )
            continue

        scan_debug["signal_found"] += 1

        score = signal.get(
            "score",
            0
        )
        trend = signal.get(
            "trend",
            "SIDEWAY"
        )

        logging.info(
            f"""
========== SIGNAL DEBUG ==========
Symbol : {symbol}
Trend : {trend}
Score : {score}
==================================
"""
        )

        minimum = (
            STOCK_MIN_SCORE
            if is_stock
            else FOREX_MIN_SCORE
        )

        if score < minimum:
            scan_debug["reject"]["score_low"] += 1
            logging.info(
                f"{symbol} REJECT SCORE {score}/{minimum}"
            )
            continue

        scan_debug["score_pass"] += 1

        if trend not in (
            "BUY",
            "SELL"
        ):
            scan_debug["reject"]["sideway"] += 1
            logging.info(
                f"{symbol} REJECT SIDEWAY"
            )
            continue

        scan_debug["trend_pass"] += 1

        best_dw = None
        primary_dw = {}
        risk = "NORMAL"
        target = "Standard"
        hold = "Intraday"

        if is_stock:
            dw_symbol = _dw_symbol_for(symbol)

            direction = (
                "CALL"
                if trend == "BUY"
                else "PUT"
            )

            cache_key = (
                f"{dw_symbol}_{direction}"
            )

            dw_list = None

            if cache_key in dw_cache:
                age = (
                    time.monotonic()
                    -
                    dw_cache[cache_key][0]
                )
                if age < DW_CACHE_TIME:
                    dw_list = (
                        dw_cache[cache_key][1]
                    )

            if dw_list is None:
                try:
                    dw_list = get_best_dw(
                        dw_symbol,
                        trend
                    )
                except Exception as e:
                    logging.exception(
                        f"{symbol} DW ERROR {e}"
                    )
                    dw_list = []

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
                scan_debug["dw_fail"] += 1
                scan_debug["reject"]["dw_fail"] += 1
                logging.info(
                    f"{symbol} REJECT : NO DW"
                )
                continue

            scan_debug["dw_pass"] += 1

            best_dw = dw_list[:3]
            primary_dw = best_dw[0]

            sens = float(
                primary_dw.get(
                    "sensitivity",
                    0
                )
                or 0
            )
            delta = float(
                primary_dw.get(
                    "abs_delta",
                    primary_dw.get(
                        "delta",
                        0
                    )
                )
                or 0
            )
            gearing = float(
                primary_dw.get(
                    "effective_gearing",
                    0
                )
                or 0
            )

            risk, target, hold = get_risk_level(
                sens,
                delta,
                gearing
            )

            logging.info(
                f"""
DW FOUND
Symbol : {symbol}
Trend : {trend}
Score : {score}
Count : {len(best_dw)}
Top DW : {primary_dw.get('symbol')}
Sens : {sens}
Delta : {delta}
Gearing : {gearing}
"""
            )
        else:
            best_dw = "FOREX"
            risk, target, hold = get_risk_level(
                0,
                0,
                0,
                True
            )

        alert_key = (
            f"{symbol}_"
            f"{trend}_"
            f"{primary_dw.get('symbol') if is_stock else 'FOREX'}"
        )

        if alert_key in last_alerts:
            if (
                current_timestamp
                -
                last_alerts[alert_key]
                <
                COOLDOWN_TIME
            ):
                logging.info(
                    f"{symbol} COOLDOWN"
                )
                continue

        last_alerts[alert_key] = current_timestamp

        message = format_dw_message(
            trend=trend,
            symbol=(
                "SET50"
                if symbol == "^SET50"
                else symbol
            ),
            dw=best_dw,
            market=market,
            price_action=signal.get(
                "price_action"
            ),
            fibo=signal.get(
                "fibonacci"
            ),
            risk=risk,
            target=target,
            hold=hold,
            score=score,
            volume_spike=signal.get("volume_spike", False)
        )

        add_candidate(
            symbol,
            message
        )

    signal_queue.clear()

    for item in candidate_signals:
        signal_queue.append(
            item["message"]
        )

    send_success = False

    logging.info(
        debug_report()
    )

    if should_send:
        send_success = send_queue()

    cleanup_cache(
        price_cache,
        dw_cache,
        last_alerts
    )

    return send_success

# ==========================================================
# RUNNER
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
                f"MAIN ERROR {e}"
            )
            time.sleep(60)


if __name__ == "__main__":
    main()
