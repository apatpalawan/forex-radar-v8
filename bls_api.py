# ==========================================================
# BLS API CLIENT V11.7 (PRODUCTION ULTIMATE FINAL)
# SET50 & MULTI-ASSET DW DATA PROVIDER
# SMART MERGE, RECOVERY, PRODUCTION LOADER & HEALTH CHECK
# ==========================================================

import logging
import time
import re
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==========================================================
# CONFIG & CONSTANTS
# ==========================================================

BASE_URL = "https://www.blswarrant.com/getapi_ajax.php"

TIMEOUT = 10
RETRY = 3
CACHE_TTL = 60
MAX_CACHE_SIZE = 300

DEFAULT_ASSETS = (
    "I",
    "F",
    "S50"
)

# Heuristic Constants for Delta Calculation
DELTA_FACTOR_HIGH = 0.45
DELTA_FACTOR_MID = 0.40
DELTA_FACTOR_LOW = 0.35
DELTA_FACTOR_MIN = 0.30


# ==========================================================
# SESSION & ADAPTER
# ==========================================================

session = requests.Session()

retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ],
    allowed_methods=["POST"]
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=20,
    pool_maxsize=20
)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update({

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",

    "Accept":
        "application/json, text/javascript, */*; q=0.01",

    "Accept-Language":
        "th,en-US;q=0.9",

    "Origin":
        "https://www.blswarrant.com",

    "Referer":
        "https://www.blswarrant.com/",

    "X-Requested-With":
        "XMLHttpRequest",

    "Connection":
        "keep-alive"

})


_cache = {}


def _clean_cache():
    """ล้าง Cache ที่หมดอายุและควบคุมขนาดสูงสุดไม่ให้เกินกำหนด (ป้องกัน Memory Leak)"""
    now = time.time()
    expired = [
        k
        for k, (t, _) in _cache.items()
        if now - t > CACHE_TTL
    ]
    for k in expired:
        _cache.pop(k, None)

    if len(_cache) > MAX_CACHE_SIZE:
        oldest = sorted(
            _cache.items(),
            key=lambda x: x[1][0]
        )
        remove = len(_cache) - MAX_CACHE_SIZE
        for k, _ in oldest[:remove]:
            _cache.pop(k, None)


# ==========================================================
# SAFE HELPERS
# ==========================================================

def safe_float(v):

    try:

        if v in ("", None, "-", "--", "N/A", "null"):

            return 0.0

        return float(
            str(v)
            .replace(",", "")
            .replace("%", "")
            .strip()
        )

    except (TypeError, ValueError):

        return 0.0



def safe_int(v):

    try:

        return int(float(v))

    except:

        return None


# ==========================================================
# CALL API
# ==========================================================

def call_bls(method, param=""):

    _clean_cache()

    key = (method, param)

    cached = _cache.get(key)

    if cached:

        ts, data = cached

        if time.time() - ts < CACHE_TTL:

            return data

    for i in range(RETRY):

        try:

            response = session.post(

                BASE_URL,

                data={

                    "method": method,

                    "param": param

                },

                timeout=TIMEOUT

            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, (dict, list)):

                raise ValueError("Invalid JSON response")

            _cache[key] = (

                time.time(),

                data

            )

            return data

        except requests.exceptions.HTTPError as e:

            code = e.response.status_code if e.response else None

            if code == 404:

                logging.error(

                    "BLS %s : HTTP 404",

                    method

                )

                return None

            logging.warning(

                "HTTP %s (%d/%d)",

                method,

                i + 1,

                RETRY

            )

        except ValueError:

            logging.warning(

                "JSON %s (%d/%d)",

                method,

                i + 1,

                RETRY

            )

        except requests.RequestException as e:

            logging.warning(

                "REQUEST %s (%d/%d) %s",

                method,

                i + 1,

                RETRY,

                e

            )

        time.sleep(min(2 ** i, 5))

    return None


# ==========================================================
# API METHODS
# ==========================================================

def get_high_sensitivity(asset):

    return call_bls(

        "getHighSensitivity",

        f"limit=200&udl_asset={asset}"

    )



def get_high_gearing(asset):

    return call_bls(

        "getHighGearing",

        f"limit=200&udl_asset={asset}"

    )



def get_low_time_decay(asset):

    return call_bls(

        "getLowTimeDecay",

        f"limit=200&udl_asset={asset}"

    )



def get_hot_dw(asset):

    return call_bls(

        "getHotDW01",

        f"limit=200&udl_asset={asset}"

    )



def get_top_gainer(asset):

    return call_bls(

        "getTopGainerDW01",

        f"limit=200&udl_asset={asset}"

    )



def get_top_loser(asset):

    return call_bls(

        "getTopLoserDW01",

        f"limit=200&udl_asset={asset}"

    )


# ==========================================================
# HELPERS
# ==========================================================

def extract_rows(data):

    if not data:
        return []

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    row_keys = (

        "data",
        "rows",
        "items",
        "result",
        "results",
        "list",

        "highSensitivityList",
        "highGearingList",
        "lowTimeDecayList",

        "hotDW01List",
        "topGainerDW01List",
        "topLoserDW01List",

    )

    for key in row_keys:

        rows = data.get(key)

        if isinstance(rows, list):

            return rows

    return []


def parse_date(date_str):

    if not date_str:

        return None

    date_str = str(date_str).strip()

    formats = (

        "%Y-%m-%d",

        "%d/%m/%Y",

        "%Y-%m-%d %H:%M:%S",

        "%d/%m/%Y %H:%M:%S",

        "%Y/%m/%d",

        "%d-%m-%Y",

    )

    for fmt in formats:

        try:

            return datetime.strptime(

                date_str,

                fmt

            )

        except ValueError:

            pass

    return None


def get_days(item, symbol):
    """
    อ่านวันหมดอายุจาก API Field ก่อน ถ้าไม่มีค่อยใช้ Regex แกะจาก Symbol
    """
    for field in ("expireDate", "expiry", "maturityDate", "expire_date", "expiryDate"):
        val = item.get(field)
        if val:
            dt = parse_date(val)
            if dt:
                days = (dt - datetime.now()).days
                return max(0, days)

    try:

        m = re.search(

            r"(\d{4})([A-Z])?$",

            symbol

        )

        if not m:

            return 90

        expiry = m.group(1)

        yy = int(expiry[:2])

        mm = int(expiry[2:])

        year = 2000 + yy

        expire_date = datetime(

            year,

            mm,

            15

        )

        now = datetime.now()

        days = (

            expire_date - now

        ).days

        if days < 0:

            return 0

        return days

    except:

        return 90


def calc_delta(sensitivity, gearing):

    sensitivity = safe_float(sensitivity)

    if sensitivity <= 0:

        return 0.0


    # =====================================
    # ESTIMATE DELTA
    # BLS ไม่มี Delta จริง
    # ใช้เป็น FILTER เท่านั้น
    # =====================================

    if sensitivity >= 1.00:

        delta = 0.55


    elif sensitivity >= 0.80:

        delta = 0.45


    elif sensitivity >= 0.60:

        delta = 0.35


    elif sensitivity >= 0.40:

        delta = 0.25


    else:

        delta = 0.15


    return round(
        delta,
        3
    )


# ==========================================================
# NORMALIZE
# ==========================================================

def normalize_dw(item):

    if not isinstance(item, dict):

        return None

    symbol = (

        item.get("secSym")

        or

        item.get("symbol")

        or ""

    ).upper()

    if not symbol:

        return None

    dw_type = str(

        item.get("dwType")

        or

        item.get("type")

        or ""

    ).upper()

    if dw_type == "C":

        dw_type = "CALL"

    elif dw_type == "P":

        dw_type = "PUT"

    underlying = (
        item.get("underlying")
        or item.get("underlyingAsset")
        or item.get("udl")
        or "SET50"
    ).upper()

    sens = safe_float(

        item.get("sensitivity")
        or item.get("sens")
        or item.get("Sensitivity")
        or item.get("SENS")
        or item.get("sensibility")
        or item.get("sensitivityValue")
        or item.get("SensitivityValue")
        or item.get("dwSensitivity")

    )

    gear = safe_float(

        item.get("effectiveGearing")
        or item.get("effGearing")
        or item.get("gearing")
        or item.get("EffectiveGearing")
        or item.get("EFFECTIVE_GEARING")
        or item.get("effectiveGearingValue")
        or item.get("eff_gearing")

    )

    raw_delta = None
    for key in (
        "delta",
        "Delta",
        "DELTA",
        "hedgeRatio",
        "hedge_ratio"
    ):
        if key in item:
            value = safe_float(item.get(key))
            if value > 0:
                raw_delta = value
                break

    delta = raw_delta if raw_delta else 0.0

    # =====================================
    # FORCE ESTIMATE DELTA
    # BLS ไม่มี Delta จริง
    # =====================================
    if delta <= 0:

        delta = calc_delta(
            sens,
            gear
        )
        
        print(
            "DELTA DEBUG:",
            symbol,
            "Sens=",
            sens,
            "Gear=",
            gear,
            "Delta=",
            delta
        )

    return {

        "symbol":
            symbol,

        "secSym":
            symbol,

        "type":
            dw_type,

        "underlying":
            underlying,

        "sensitivity":
            sens,

        "effective_gearing":
            gear,

        "delta":
            delta,

        "abs_delta":
            abs(delta),

        "days_left":
            get_days(item, symbol),

        "spread":
            safe_float(

                item.get("spread")
                or item.get("bidAskSpread")
                or item.get("spreadPercent")

            ),

        "time_decay":
            safe_float(

                item.get("timeDecay")
                or item.get("theta")
                or item.get("time_decay")

            )

    }


# ==========================================================
# LOAD ALL
# ==========================================================

def get_all_set50_dw():

    result = {}

    funcs = (

        get_high_sensitivity,

        get_high_gearing,

        get_low_time_decay,

        get_hot_dw,

        get_top_gainer,

        get_top_loser

    )

    for asset in DEFAULT_ASSETS:

        for func in funcs:

            logging.info("%s -> %s", asset, func.__name__)

            data = func(asset)

            for row in extract_rows(data):

                dw = normalize_dw(row)

                if not dw:

                    continue

                symbol = dw["symbol"]

                if symbol not in result:

                    result[symbol] = dw

                else:

                    old = result[symbol]

                    for k, v in dw.items():

                        if v not in (None, "", 0, 0.0):

                            if old.get(k) in (None, "", 0, 0.0):

                                old[k] = v

                            elif k in (
                                "sensitivity",
                            ) and v > old.get(k, 0):

                                old[k] = v

                    if old.get("delta") in (None, 0, 0.0) and dw.get("delta", 0) > 0:
                        old["delta"] = dw["delta"]

                    if old.get("spread", 0) <= 0 and dw.get("spread", 0) > 0:
                        old["spread"] = dw["spread"]

                    if old.get("time_decay", 0) <= 0 and dw.get("time_decay", 0) > 0:
                        old["time_decay"] = dw["time_decay"]

                    if old.get("days_left", 0) in (None, 0):
                        if v := dw.get("days_left"):
                            old["days_left"] = v
                    else:
                        if (v := dw.get("days_left")) and v > 0:
                            old["days_left"] = min(old["days_left"], v)

    for dw in result.values():
        dw["abs_delta"] = abs(dw.get("delta", 0))

    final = list(result.values())

    logging.info(

        f"BLS MERGED DW : {len(final)}"

    )

    return final


# ==========================================================
# DATA QUALITY FILTER V11.7
# ตรวจสอบความสมบูรณ์ของ DW ก่อนส่ง Scanner
# ==========================================================

def validate_dw(dw):

    """
    ตรวจสอบข้อมูล DW ขั้นพื้นฐาน

    ไม่ตัดสินใจซื้อขาย
    ทำหน้าที่กันข้อมูลเสียจาก API
    """

    if not isinstance(dw, dict):

        return False


    symbol = dw.get("symbol", "")

    if not symbol:

        return False


    # ต้องมี Sensitivity
    if dw.get("sensitivity", 0) <= 0:

        return False


    # ต้องมี Gearing
    if dw.get("effective_gearing", 0) <= 0:

        return False


    # Delta ต้องสมเหตุสมผล

    delta = abs(
        safe_float(
            dw.get("delta")
        )
    )


    if delta > 1.5:

        return False


    # อายุคงเหลือ
    days = safe_int(
        dw.get("days_left")
    )


    if days is not None:

        if days <= 0:

            return False


    return True


# ==========================================================
# FILTER DW LIST
# ==========================================================

def filter_valid_dw(dw_list):

    """
    คืนเฉพาะ DW ที่ข้อมูลพร้อมใช้งาน
    """

    if not dw_list:

        return []


    result = []


    for dw in dw_list:

        try:

            if validate_dw(dw):

                result.append(dw)

        except Exception:

            continue


    logging.info(

        "VALID DW : %d / %d",

        len(result),

        len(dw_list)

    )


    return result


# ==========================================================
# REMOVE DUPLICATE SYMBOL
# ==========================================================

def unique_dw(dw_list):

    """
    กัน DW ซ้ำ
    """

    seen = set()

    result = []


    for dw in dw_list:

        symbol = dw.get(
            "symbol"
        )


        if symbol in seen:

            continue


        seen.add(symbol)

        result.append(dw)


    return result


# ==========================================================
# SET50 DW IDENTIFIER
# ==========================================================

def is_set50_dw(dw):

    """
    ตรวจว่าเป็น DW ที่อ้างอิง SET50 หรือไม่

    รองรับหลายชื่อจาก BLS
    """

    underlying = str(

        dw.get(
            "underlying",
            ""

        )

    ).upper()


    symbol = str(

        dw.get(
            "symbol",
            ""

        )

    ).upper()


    keywords = (

        "SET50",

        "S50",

        "SET"

    )


    for k in keywords:

        if k in underlying:

            return True


    # fallback จากชื่อ Symbol

    if symbol.startswith(
        "SET50"
    ):

        return True


    return False


# ==========================================================
# FILTER ASSET
# ==========================================================

def filter_asset(dw_list, asset="SET50"):

    """
    แยกสินทรัพย์

    ใช้ต่อกับ Scanner
    """

    if not dw_list:

        return []


    asset = asset.upper()


    result = []


    for dw in dw_list:


        if asset == "SET50":

            if is_set50_dw(dw):

                result.append(dw)


        else:

            if dw.get(
                "underlying"
            ) == asset:

                result.append(dw)



    return result


# ==========================================================
# NORMALIZE FINAL OUTPUT
# ==========================================================

def prepare_dw_data():

    """
    Pipeline หลัก

    API
     |
     v
    Normalize
     |
     v
    Validate
     |
     v
    Unique
     |
     v
    Ready Scanner

    """


    raw = get_all_set50_dw()


    valid = filter_valid_dw(
        raw
    )


    unique = unique_dw(
        valid
    )


    final = filter_asset(
        unique,
        "SET50"
    )


    logging.info(

        "READY DW DATA : %d",

        len(final)

    )


    return final


# ==========================================================
# QUICK LOOKUP
# ==========================================================

def get_dw_by_symbol(symbol):

    """
    ค้นหา DW รายตัว

    """

    symbol = str(
        symbol
    ).upper()


    data = prepare_dw_data()


    for dw in data:

        if dw.get(
            "symbol"
        ) == symbol:

            return dw


    return None


# ==========================================================
# DEBUG EXPORT
# ==========================================================

def print_dw_summary(dw_list, limit=10):


    if not dw_list:

        print(
            "NO DATA"
        )

        return



    print(
        ""
    )

    print(
        "=" * 60
    )

    print(
        "BLS DW SUMMARY"
    )

    print(
        "=" * 60
    )


    for dw in dw_list[:limit]:


        print(

            f"{dw['symbol']} | "
            f"{dw['type']} | "
            f"Sens={dw['sensitivity']} | "
            f"Gear={dw['effective_gearing']} | "
            f"Delta={dw['delta']} | "
            f"Days={dw['days_left']}"

        )


# ==========================================================
# ADVANCED DW ANALYTICS V11.7
# STRUCTURE DATA FOR SCANNER
# ==========================================================

def get_dw_type(dw):

    """
    คืนประเภท CALL / PUT
    """

    dw_type = str(

        dw.get(
            "type",
            ""

        )

    ).upper()


    if dw_type in (
        "C",
        "CALL"
    ):

        return "CALL"


    if dw_type in (
        "P",
        "PUT"
    ):

        return "PUT"


    return "UNKNOWN"


# ==========================================================
# DELTA PROFILE
# ==========================================================

def delta_profile(delta):

    """
    แปลง Delta เป็นระดับความไว

    ใช้ประกอบการกรอง
    ไม่ใช่คะแนน
    """

    delta = abs(
        safe_float(delta)
    )


    if delta >= 0.80:

        return "HIGH"


    if delta >= 0.50:

        return "MEDIUM"


    if delta >= 0.30:

        return "LOW"


    return "VERY_LOW"


# ==========================================================
# SENSITIVITY PROFILE
# ==========================================================

def sensitivity_profile(value):

    sens = safe_float(value)


    if sens >= 1.10:

        return "VERY_HIGH"


    if sens >= 1.00:

        return "HIGH"


    if sens >= 0.80:

        return "NORMAL"


    return "LOW"


# ==========================================================
# GEARING PROFILE
# ==========================================================

def gearing_profile(value):


    gear = safe_float(value)


    if gear >= 10:

        return "HIGH"


    if gear >= 5:

        return "MEDIUM"


    return "LOW"


# ==========================================================
# TIME RISK PROFILE
# ==========================================================

def time_profile(days):

    days = safe_int(days)


    if days is None:

        return "UNKNOWN"


    if days < 14:

        return "VERY_HIGH"


    if days < 30:

        return "HIGH"


    if days < 60:

        return "MEDIUM"


    return "LOW"


# ==========================================================
# LIQUIDITY CHECK
# ==========================================================

def liquidity_flag(dw):

    """
    ตรวจสอบความเสี่ยง Spread

    ไม่ตัดสินใจ
    แค่บอกสถานะ
    """

    spread = safe_float(

        dw.get(
            "spread"
        )

    )


    if spread <= 0:

        return "UNKNOWN"


    if spread <= 0.01:

        return "GOOD"


    if spread <= 0.03:

        return "NORMAL"


    return "WIDE"


# ==========================================================
# ENRICH DW DATA
# ==========================================================

def enrich_dw(dw):

    """
    เพิ่มข้อมูลวิเคราะห์

    """

    if not isinstance(dw, dict):

        return None


    data = dict(dw)


    data["dw_type"] = get_dw_type(
        data
    )


    data["delta_level"] = delta_profile(

        data.get(
            "delta"
        )

    )


    data["sensitivity_level"] = sensitivity_profile(

        data.get(
            "sensitivity"
        )

    )


    data["gearing_level"] = gearing_profile(

        data.get(
            "effective_gearing"
        )

    )


    data["time_risk"] = time_profile(

        data.get(
            "days_left"
        )

    )


    data["liquidity"] = liquidity_flag(

        data

    )


    return data


# ==========================================================
# ENRICH PIPELINE
# ==========================================================

def enrich_dw_list(dw_list):

    """
    เพิ่มข้อมูลให้ DW ทั้งชุด
    """

    result = []


    for dw in dw_list:


        try:

            item = enrich_dw(
                dw
            )


            if item:

                result.append(
                    item
                )


        except Exception as e:

            logging.warning(

                "ENRICH FAIL %s",

                e

            )


    return result


# ==========================================================
# FINAL DATA PROVIDER
# ==========================================================

def get_ready_dw():

    """
    Function หลักสำหรับ Scanner

    ใช้ตัวนี้เรียกจาก dw_scanner.py

    """

    data = prepare_dw_data()


    data = enrich_dw_list(

        data

    )


    logging.info(

        "FINAL PROVIDER DATA : %d",

        len(data)

    )


    return data


# ==========================================================
# SEARCH CALL / PUT
# ==========================================================

def filter_dw_type(dw_list, dw_type):

    """
    แยก CALL / PUT
    """

    dw_type = dw_type.upper()


    return [

        dw

        for dw in dw_list

        if dw.get(
            "dw_type"
        ) == dw_type

    ]


def get_call_dw():

    return filter_dw_type(

        get_ready_dw(),

        "CALL"

    )


def get_put_dw():

    return filter_dw_type(

        get_ready_dw(),

        "PUT"

    )


# ==========================================================
# SCANNER PAYLOAD FORMAT
# ==========================================================

def scanner_payload(dw):

    """
    รูปแบบข้อมูลส่งให้ DW Scanner

    """

    return {

        "symbol":
            dw.get("symbol"),


        "type":
            dw.get("dw_type"),


        "underlying":
            dw.get("underlying"),


        "sensitivity":
            dw.get("sensitivity"),


        "gearing":
            dw.get("effective_gearing"),


        "delta":
            dw.get("delta"),


        "days":
            dw.get("days_left"),


        "spread":
            dw.get("spread"),


        "delta_level":
            dw.get("delta_level"),


        "liquidity":
            dw.get("liquidity"),


        "time_risk":
            dw.get("time_risk")

    }


def build_scanner_dataset():

    """
    Dataset พร้อมเข้า dw_scanner.py
    """

    data = get_ready_dw()


    result = []


    for dw in data:

        result.append(

            scanner_payload(dw)

        )


    return result


# ==========================================================
# SCANNER INTERFACE V11.7
# CONNECTION LAYER FOR DW SCANNER
# ==========================================================

def safe_get(dw, key, default=0):

    """
    อ่านค่าแบบปลอดภัย
    """

    if not isinstance(dw, dict):

        return default


    value = dw.get(key)


    if value in (
        None,
        "",
        "-",
    ):

        return default


    return value


# ==========================================================
# DW SCANNER RECORD
# ==========================================================

def create_scanner_record(dw):

    """
    แปลงข้อมูล BLS
    เป็นรูปแบบที่ Scanner ใช้

    ไม่มี Score
    ไม่มี Buy/Sell
    """

    return {


        # Identity

        "symbol":
            safe_get(
                dw,
                "symbol",
                ""
            ),


        "underlying":
            safe_get(
                dw,
                "underlying",
                ""
            ),


        "type":
            safe_get(
                dw,
                "dw_type",
                ""
            ),



        # Core DW Data

        "sensitivity":
            safe_float(
                safe_get(
                    dw,
                    "sensitivity"
                )
            ),


        "effective_gearing":
            safe_float(
                safe_get(
                    dw,
                    "effective_gearing"
                )
            ),


        "delta":
            safe_float(
                safe_get(
                    dw,
                    "delta"
                )
            ),



        # Risk

        "days_left":
            safe_int(
                safe_get(
                    dw,
                    "days_left"
                )
            ),


        "spread":
            safe_float(
                safe_get(
                    dw,
                    "spread"
                )
            ),



        # Analysis Flags

        "delta_level":
            safe_get(
                dw,
                "delta_level",
                "UNKNOWN"
            ),


        "sensitivity_level":
            safe_get(
                dw,
                "sensitivity_level",
                "UNKNOWN"
            ),


        "gearing_level":
            safe_get(
                dw,
                "gearing_level",
                "UNKNOWN"
            ),


        "liquidity":
            safe_get(
                dw,
                "liquidity",
                "UNKNOWN"
            ),


        "time_risk":
            safe_get(
                dw,
                "time_risk",
                "UNKNOWN"
            )

    }


# ==========================================================
# BUILD SCANNER DATA
# ==========================================================

def get_scanner_data():

    """
    Function หลักที่ dw_scanner.py เรียก

    """

    data = get_ready_dw()


    result = []


    for dw in data:


        try:

            record = create_scanner_record(
                dw
            )


            if record["symbol"]:

                result.append(
                    record
                )


        except Exception as e:

            logging.warning(

                "SCANNER RECORD FAIL : %s",

                e

            )


    logging.info(

        "SCANNER READY : %d",

        len(result)

    )


    return result


# ==========================================================
# FILTER HELPERS
# ==========================================================

def get_call_scanner_data():

    """
    เฉพาะ CALL
    """

    return [

        x

        for x in get_scanner_data()

        if x.get(
            "type"
        ) == "CALL"

    ]


def get_put_scanner_data():

    """
    เฉพาะ PUT
    """

    return [

        x

        for x in get_scanner_data()

        if x.get(
            "type"
        ) == "PUT"

    ]


# ==========================================================
# SYMBOL SEARCH CACHE
# ==========================================================

_symbol_cache = {}


def build_symbol_cache():

    """
    สร้าง index
    ลดเวลาค้นหา DW

    """

    global _symbol_cache


    _symbol_cache = {}


    for dw in get_scanner_data():

        symbol = dw.get(
            "symbol"
        )


        if symbol:

            _symbol_cache[symbol] = dw



    return _symbol_cache


def find_dw(symbol):

    """
    ค้นหา DW รายตัว

    """

    symbol = str(
        symbol
    ).upper()



    if not _symbol_cache:

        build_symbol_cache()



    return _symbol_cache.get(
        symbol
    )


# ==========================================================
# MARKET SIDE FILTER
# ==========================================================

def filter_market_side(dw_list, side):

    """
    side:

    CALL
    PUT

    """

    side = str(
        side
    ).upper()


    if side not in (
        "CALL",
        "PUT"
    ):

        return []


    return [

        dw

        for dw in dw_list

        if dw.get(
            "type"
        ) == side

    ]


# ==========================================================
# MINIMUM DATA CHECK
# ==========================================================

def scanner_ready(dw):

    """
    ตรวจสอบก่อนเข้า Ranking

    """

    required = (

        "symbol",

        "sensitivity",

        "effective_gearing",

        "delta"

    )


    for key in required:


        if dw.get(key) in (
            None,
            "",
            0
        ):

            return False


    return True


def remove_bad_scanner_data(data):

    result = []


    for dw in data:


        if scanner_ready(dw):

            result.append(dw)


    logging.info(

        "AFTER SCANNER CHECK : %d",

        len(result)

    )


    return result


# ==========================================================
# FINAL EXPORT FUNCTION
# ==========================================================

def load_dw_for_scanner():

    """
    จุดเชื่อมหลักกับ dw_scanner.py

    """

    data = get_scanner_data()


    data = remove_bad_scanner_data(
        data
    )


    return data


# ==========================================================
# DEBUG
# ==========================================================

def debug_scanner_data(limit=10):

    data = load_dw_for_scanner()


    print()

    print(
        "=" * 70
    )

    print(
        "DW SCANNER DATA"
    )

    print(
        "=" * 70
    )


    for dw in data[:limit]:


        print(

            dw["symbol"],

            "|",

            dw["type"],

            "| Sens",

            dw["sensitivity"],

            "| Delta",

            dw["delta"],

            "| Gear",

            dw["effective_gearing"],

            "| Days",

            dw["days_left"]

        )


# ==========================================================
# SMART MERGE ENGINE V11.7
# MERGE MULTIPLE BLS SOURCE WITH DATA RECOVERY
# ==========================================================

def merge_dw_field(target, source):

    """
    เติมข้อมูลที่ขาด
    ไม่เขียนทับค่าที่ดีกว่า
    """

    if not isinstance(target, dict):

        return source


    if not isinstance(source, dict):

        return target



    for key, value in source.items():


        if value in (
            None,
            "",
            0,
            0.0
        ):

            continue



        old = target.get(
            key
        )


        # เติมช่องว่าง

        if old in (
            None,
            "",
            0,
            0.0
        ):

            target[key] = value



        # Sensitivity เอาค่าสูงกว่า

        elif key == "sensitivity" and value > old:
            target[key] = value
            
        elif key == "effective_gearing" and value > old:
            target[key] = value
            
        elif key == "delta" and value > 0 and (old <= 0 or old is None):
            target[key] = value

    return target