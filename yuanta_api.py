# ==========================================================
# YUANTA API CLIENT V1.0
# DW19 CLUB (dw19club.com) - Yuanta DW Screener
# แหล่งข้อมูล: https://www.dw19club.com/api/search/advance
# (หา endpoint นี้ผ่าน Chrome DevTools -> Network -> Fetch/XHR)
# ==========================================================

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==========================================================
# CONFIG & CONSTANTS
# ==========================================================

BASE_URL = "https://www.dw19club.com/api/search/advance"

TIMEOUT = 10
RETRY = 3
CACHE_TTL = 60

# Yuanta ไม่มี Delta จริงในข้อมูลที่ตอบกลับมา (เหมือน BLS)
# ใช้ประมาณค่าแบบเดียวกับที่ bls_api.py ทำ เพื่อให้ dw_scanner.py
# กรอง/เทียบกันข้ามค่ายได้อย่างสมเหตุสมผล
DELTA_BUCKET = (
    (1.00, 0.55),
    (0.80, 0.45),
    (0.60, 0.35),
    (0.40, 0.25),
    (0.00, 0.15),
)


# ==========================================================
# SESSION & ADAPTER
# ==========================================================

session = requests.Session()

retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"],
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=20,
    pool_maxsize=20,
)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "th,en-US;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://www.dw19club.com",
        "Referer": "https://www.dw19club.com/search",
        "Connection": "keep-alive",
    }
)


_cache = {}


def _clean_cache():
    now = time.time()
    dead = [k for k, (ts, _) in _cache.items() if now - ts > CACHE_TTL * 5]
    for k in dead:
        _cache.pop(k, None)


# ==========================================================
# SAFE
# ==========================================================

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0


# ==========================================================
# DELTA ESTIMATE (Yuanta ไม่มี Delta จริงเหมือนกับ BLS)
# ==========================================================

def calc_delta(sensitivity):
    sensitivity = safe_float(sensitivity)

    if sensitivity <= 0:
        return 0.0

    for threshold, delta in DELTA_BUCKET:
        if sensitivity >= threshold:
            return delta

    return 0.15


# ==========================================================
# EXTRACT LIST OF DW RECORDS FROM RESPONSE
# (ไม่ fix โครง JSON แน่นอน เผื่อ Response ห่อ key ต่างจากที่เจอตอนทดสอบ)
# ==========================================================

def _extract_list(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # ลองหา key ที่มักใช้ห่อ list ของข้อมูลก่อน
        for key in ("data", "list", "rows", "result", "results", "items", "records"):
            value = data.get(key)

            if isinstance(value, list):
                return value

            if isinstance(value, dict):
                nested = _extract_list(value)
                if nested:
                    return nested

        # เผื่อกรณี response เป็น dict แต่ list อยู่ลึกกว่านั้น
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value

            if isinstance(value, dict):
                nested = _extract_list(value)
                if nested:
                    return nested

    return []


# ==========================================================
# CALL API
# ==========================================================

def call_yuanta(underlying="SET50", limit=500):
    _clean_cache()

    key = (underlying, limit)
    cached = _cache.get(key)

    if cached:
        ts, data = cached
        if time.time() - ts < CACHE_TTL:
            return data

    payload = {
        "underlying": underlying,
        "callorput": "",
        "issuer": ["All"],
        "gearing_start": "",
        "gearing_end": "",
        "days_ltd_start": "",
        "days_ltd_end": "",
        "moneyness_start": "",
        "moneyness_end": "",
        "price_start": "",
        "price_end": "",
        "sensitivity_start": "",
        "sensitivity_end": "",
        "limit": limit,
        "offset": 1,
    }

    for i in range(RETRY):
        try:
            response = session.post(
                BASE_URL,
                json=payload,
                timeout=TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            _cache[key] = (time.time(), data)

            return data

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else None

            if code == 404:
                logging.error("YUANTA %s : HTTP 404", underlying)
                return None

            logging.warning("YUANTA HTTP ERROR %s (%d/%d)", underlying, i + 1, RETRY)

        except ValueError:
            logging.warning("YUANTA JSON ERROR %s (%d/%d)", underlying, i + 1, RETRY)

        except requests.RequestException as e:
            logging.warning("YUANTA REQUEST ERROR %s (%d/%d) %s", underlying, i + 1, RETRY, e)

        time.sleep(min(2 ** i, 5))

    return None


# ==========================================================
# NORMALIZE
# แปลงเป็น format เดียวกับที่ dw_scanner.py ใช้อยู่แล้ว
# (ต้องตรงกับ record ที่ bls_api.create_scanner_record ส่งออกมา)
# ==========================================================

def normalize_dw(item, underlying):
    if not isinstance(item, dict):
        return None

    symbol = str(item.get("symbol", "")).upper()

    if not symbol:
        return None

    raw_type = str(item.get("type", "")).upper()

    if raw_type == "C":
        dw_type = "CALL"
    elif raw_type == "P":
        dw_type = "PUT"
    else:
        dw_type = raw_type

    sens = safe_float(item.get("sen"))
    gearing = safe_float(item.get("gearing"))

    # Yuanta ไม่ส่ง Delta จริงมา (เหมือน BLS) -> ประมาณค่าแบบเดียวกัน
    delta = calc_delta(sens)

    return {
        "symbol": symbol,
        "underlying": str(underlying).upper(),
        "type": dw_type,
        "issuer": str(item.get("issuer", "YUANTA")).upper(),
        "sensitivity": sens,
        "effective_gearing": gearing,
        "delta": delta,
        "abs_delta": abs(delta),
        "days_left": safe_int(item.get("ltd")),
        # dw19club ไม่ส่ง spread/liquidity มาตรง ๆ -> ใช้ค่า default
        # ที่ pass_filter() ใน dw_scanner.py ปฏิบัติเป็น "ไม่ตัดออก"
        "spread": safe_float(item.get("spread")),
        "liquidity": str(item.get("liquidity", "")).upper(),
        # ข้อมูลเสริมสำหรับแสดงผล (dw_formatter.py จะโชว์ถ้ามี)
        "iv": item.get("implied_vol"),
        "price": safe_float(item.get("price")),
        "exercise_price": safe_float(item.get("exercise_price")),
        "moneyness": safe_float(item.get("moneyness")),
        "ratio": safe_float(item.get("ratio")),
        "last_trade": item.get("last_trade"),
    }


# ==========================================================
# PUBLIC: ใช้เป็นตัวเดียวกับ bls_api.get_scanner_data()
# dw_scanner.py เรียกใช้ตัวนี้เพิ่ม แล้วเอาไปรวมกับของ BLS
# ==========================================================

def get_dw_by_underlying(underlying="SET50"):
    raw = call_yuanta(underlying=underlying)

    if not raw:
        logging.warning("NO YUANTA DW DATA (%s)", underlying)
        return []

    items = _extract_list(raw)

    result = []

    for item in items:
        try:
            record = normalize_dw(item, underlying)

            if record:
                result.append(record)

        except Exception as e:
            logging.warning("YUANTA RECORD FAIL : %s", e)

    logging.info("YUANTA READY (%s) : %d", underlying, len(result))

    return result
