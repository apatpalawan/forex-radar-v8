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
    "11:30",
    "14:35",
    "16:30"
]

# ==========================================
# THAI STOCK LIST
# ==========================================
# ขยายจาก 11 ตัวเดิม เป็นสมาชิก SET50 ทั้งหมด (รอบ 2H/2026,
# มีผล ก.ค.-ธ.ค. 2569) เพื่อสแกนหาหุ้นที่มี DW ให้ครอบคลุมมากขึ้น
# (หุ้นที่มี DW เกือบทั้งหมดอยู่ใน SET50/SET100 อยู่แล้ว)
#
# รายชื่อนี้ตรวจสอบจากแหล่งข้อมูลสาธารณะได้ 49 จาก 50 ตัว
# ตัวที่ 50 หาไม่พบชัดเจน แนะนำให้เช็คซ้ำและเพิ่มเองที่
# https://www.settrade.com/th/equities/market-data/index-list/SET50
# (รายชื่อทางการ อัปเดตทุก 6 เดือน)
#
# หมายเหตุ: เพิ่มจาก 11 -> 49 ตัว ทำให้แต่ละรอบสแกนใช้เวลานานขึ้น
# (ประมาณ 2-3 นาที จากเดิมไม่ถึง 1 นาที) ยังอยู่ในขอบเขต 10 นาที
# ที่ GitHub Actions ให้ต่อรอบ (timeout-minutes ใน .github/workflows/
# forex-radar.yml) ไม่ต้องปรับ timeout เพิ่ม
STOCKS = [
    "ADVANC", "AOT", "AWC", "BBL", "BCP", "BDMS", "BEM", "BH", "BJC",
    "CCET", "COM7", "CPALL", "CPF", "CPN", "CRC", "DELTA", "EGCO",
    "GPSC", "GULF", "HMPRO", "IVL", "KBANK", "KKP", "KTB", "KTC",
    "LH", "MINT", "MRDIYT", "MTC", "OR", "OSP", "PTT", "PTTEP",
    "PTTGC", "RATCH", "SCB", "SCC", "SCGP", "TCAP", "TFG", "THAI",
    "TIDLOR", "TISCO", "TLI", "TOP", "TRUE", "TTB", "TU", "WHA"
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
