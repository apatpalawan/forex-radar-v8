# ==========================================
# FOREX RADAR V9 PROFESSIONAL
# CONFIGURATION
# ==========================================


# ==========================================
# VERSION
# ==========================================

VERSION = "9.0"



# ==========================================
# SCAN SETTINGS
# ==========================================

SCAN_INTERVAL = 60



# ==========================================
# LINE NOTIFY SEND TIME
# ==========================================

SEND_TIMES = [
    "09:10",
    "10:30",
    "12:00",
    "14:00",
    "15:30",
    "16:45"
]



# ==========================================
# THAI STOCK LIST
# ==========================================

STOCKS = [
    "ADVANC",
    "AOT",
    "KBANK",
    "SCB",
    "BBL",
    "PTT",
    "PTTEP",
    "CPALL",
    "DELTA",
    "GULF",
    "CPN"
]



# ==========================================
# FOREX LIST
# ==========================================

FOREX = [
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY"
]



# ==========================================
# YAHOO FINANCE TICKER MAP
# ==========================================

TICKER_MAP = {

    "^SET50": "TDEX.BK",

    "XAUUSD": "GC=F",

    "EURUSD": "EURUSD=X",

    "GBPUSD": "GBPUSD=X",

    "USDJPY": "JPY=X"

}



# ==========================================
# DW SETTINGS
#
# DW = FILTER ONLY
#
# ไม่ให้คะแนน
# ไม่เลือกตัวชนะ
# ไม่ใช้ Hybrid Score
#
# ==========================================


USE_SET_DW_API = False


DW_API_TIMEOUT = 15

DW_API_DELAY = 0.2

DW_MAX_WORKERS = 8


DW_DEBUG = True



# ==========================================
# DW ISSUER FILTER
# ==========================================

ALLOWED_DW_ISSUERS = [

    "BLS",
    "YUANTA"

]



# ==========================================
# DW QUALITY FILTER
# ==========================================

MIN_SENSITIVITY = 1.0

MIN_DELTA = 0.30

MIN_GEARING = 5

MAX_SPREAD = 0.02

MIN_DAYS_LEFT = 30



# ==========================================
# LEGACY SCORE
#
# V9 ไม่ใช้ DW Score แล้ว
# เก็บไว้ป้องกัน Module เก่า Error
# ==========================================

MIN_DW_SCORE = None



# ==========================================
# FALLBACK FILTER
# ==========================================

DW_FALLBACK_SENSITIVITY = 0.95



# ==========================================
# ISSUER PRIORITY
# ==========================================

PREFERRED_ISSUER_WEIGHT = {

    "BLS": 5,

    "YUANTA": 5

}



# ==========================================
# CACHE SETTINGS
# ==========================================

PRICE_CACHE_TTL = 300

DW_CACHE_TTL = 900

MAX_ALERT_MEMORY = 200



# ==========================================
# MARKET DATA SETTINGS
# ==========================================

TIMEFRAME = "1d"

LOOKBACK = 700



# ==========================================
# THAI MARKET TIME
# ==========================================

MARKET_OPEN_HOUR = 9

MARKET_OPEN_MINUTE = 0

MARKET_CLOSE_HOUR = 17

MARKET_CLOSE_MINUTE = 0



# ==========================================
# RISK MANAGEMENT
# ==========================================

RISK_SETTINGS = {

    "MAX_POSITION": 0.05,

    "STOP_LOSS_PERCENT": 3,

    "TAKE_PROFIT_PERCENT": 6

}



# ==========================================
# SYMBOL NORMALIZE
# ==========================================

SYMBOL_ALIAS = {

    "^SET50.BK": "SET50",

    "^SET50": "SET50"

}



# ==========================================
# DW ISSUER API
# ==========================================

DW_ISSUER_API = {

    "BLS": {
        "enabled": True
    },

    "YUANTA": {
        "enabled": True
    },

    "KGI": {
        "enabled": False
    },

    "MACQ": {
        "enabled": False
    },

    "CGSI": {
        "enabled": False
    },

    "JPM": {
        "enabled": False
    }

}
