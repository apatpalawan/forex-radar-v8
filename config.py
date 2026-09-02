# ==========================================
# FOREX RADAR V8.6 PROFESSIONAL
# CONFIGURATION
# ==========================================

# Version
VERSION = "8.6"

# ==========================================
# SCAN SETTINGS
# ==========================================
SCAN_INTERVAL = 60

# ==========================================
# LINE NOTIFY SEND TIME
# ==========================================
SEND_TIMES = [
    "10:30",
    "14:35",
    "19:00"
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
    # SET50 (ใช้ TDEX.BK ETF แทน ^SET50.BK ดิบ - ดูเหตุผลใน data_loader.py)
    "^SET50":
        "TDEX.BK",

    # GOLD
    "XAUUSD":
        "GC=F",

    # FOREX
    "EURUSD":
        "EURUSD=X",
    "GBPUSD":
        "GBPUSD=X",
    "USDJPY":
        "JPY=X"
}

# ==========================================
# DW SETTINGS
# ==========================================

# ==========================================
# DW API SETTINGS
# ==========================================

# ใช้ API ของผู้ออก DW แทน SET
USE_SET_DW_API = False

# โหลดข้อมูลจากผู้ออก DW พร้อมกัน
DW_API_TIMEOUT = 15

# หน่วงเวลาระหว่างเรียก API (วินาที)
DW_API_DELAY = 0.2

# จำนวน Thread สำหรับโหลดข้อมูล
DW_MAX_WORKERS = 8

# เปิด Debug
DW_DEBUG = True

# เลือกเฉพาะผู้ออก DW
# BLS = บัวหลวง
# YUANTA = หยวนต้า
ALLOWED_DW_ISSUERS = [
    "BLS",
    "YUANTA"
]

# Minimum DW Quality Filter
MIN_SENSITIVITY = 1.0
MIN_DELTA = 0.30
MIN_GEARING = 5
MAX_SPREAD = 0.02
MIN_DAYS_LEFT = 30
MIN_DW_SCORE = 75

# Fallback Filter
DW_FALLBACK_SENSITIVITY = 0.95

# Issuer Priority Weight
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
# DATA SETTINGS
# ==========================================
TIMEFRAME = "1d"
LOOKBACK = 700

# ==========================================
# VOLUME ANOMALY SCANNER
# ==========================================
# Volume แท่งล่าสุด >= กี่เท่าของค่าเฉลี่ย Volume ย้อนหลัง 20 วัน
# (VOL_MA20) ถึงจะถือว่า "ผิดปกติ" และเริ่มหา DW ให้
# ปรับตัวเลขนี้ได้ตามความไวที่ต้องการ (2.0 = สูงกว่าปกติ 2 เท่า)
ABNORMAL_VOLUME_RATIO = 2.0

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
    "MAX_POSITION":
        0.05,
    "STOP_LOSS_PERCENT":
        3,
    "TAKE_PROFIT_PERCENT":
        6
}

# ==========================================
# SYMBOL NORMALIZE
# ==========================================
SYMBOL_ALIAS = {
    "^SET50.BK":
        "SET50",
    "^SET50":
        "SET50"
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
