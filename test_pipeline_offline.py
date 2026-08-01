# ==========================================================
# OFFLINE MOCK TEST - ไม่ต้องต่อ internet เลย
#
# ทดสอบเฉพาะจุดที่แก้ไปในรอบนี้:
# 1) dw_scanner.py import ถูกต้องแล้ว (get_scanner_data)
# 2) get_filtered_dw() กรองตาม "underlying" จริง (บั๊กเดิม: ไม่กรอง)
# 3) format_dw_message() ยังไม่พังหลังตัดระบบ score ออก
# 4) get_risk_level() (Main.py) ยังจัดหมวดถูกต้อง
#
# วิธีรัน:
#   python3 test_pipeline_offline.py
# ==========================================================

import sys
import dw_scanner
import dw_formatter
import Main


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        print(f"[PASS] {name}")
        PASS += 1
    else:
        print(f"[FAIL] {name}")
        FAIL += 1


# ==========================================================
# FIXTURE: DW จำลอง (แทนของจริงจาก bls_api.get_scanner_data())
# มีทั้ง PTT และ KBANK ปนกัน เพื่อทดสอบว่า filter ตาม underlying
# ทำงานจริง (นี่คือบั๊กที่เจอและแก้ไปแล้ว)
# ==========================================================

FAKE_SCANNER_DATA = [
    # PTT CALL ผ่านเกณฑ์ทุกอย่าง -> ควรถูกเลือก
    {
        "symbol": "PTT01C2611A",
        "underlying": "PTT",
        "type": "CALL",
        "sensitivity": 1.10,
        "delta": 0.60,
        "effective_gearing": 9.0,
        "days_left": 82,
        "spread": 0.01,
        "liquidity": "NORMAL",
    },
    # PTT CALL แต่ Sensitivity ต่ำกว่าเกณฑ์ (0.95) -> ต้องถูกตัดออก
    {
        "symbol": "PTT01C2611B",
        "underlying": "PTT",
        "type": "CALL",
        "sensitivity": 0.50,
        "delta": 0.60,
        "effective_gearing": 9.0,
        "days_left": 82,
        "spread": 0.01,
        "liquidity": "NORMAL",
    },
    # KBANK CALL คุณภาพดีกว่า PTT ทุกอย่าง แต่คนละ underlying
    # -> ถ้าบั๊กเดิมยังอยู่ ตัวนี้จะหลุดเข้ามาปนตอนขอ DW ของ PTT
    {
        "symbol": "KBANK19C2611A",
        "underlying": "KBANK",
        "type": "CALL",
        "sensitivity": 1.50,
        "delta": 0.90,
        "effective_gearing": 15.0,
        "days_left": 90,
        "spread": 0.005,
        "liquidity": "NORMAL",
    },
    # PTT PUT -> ไม่ควรถูกเลือกตอนขอ CALL (trend=BUY)
    {
        "symbol": "PTT01P2611A",
        "underlying": "PTT",
        "type": "PUT",
        "sensitivity": 1.10,
        "delta": -0.60,
        "effective_gearing": 9.0,
        "days_left": 82,
        "spread": 0.01,
        "liquidity": "NORMAL",
    },
    # PTT CALL แต่ liquidity แย่ (WIDE) -> ต้องถูกตัดออก
    {
        "symbol": "PTT01C2611C",
        "underlying": "PTT",
        "type": "CALL",
        "sensitivity": 1.20,
        "delta": 0.65,
        "effective_gearing": 9.5,
        "days_left": 82,
        "spread": 0.01,
        "liquidity": "WIDE",
    },
]


def fake_get_scanner_data():
    return FAKE_SCANNER_DATA


# ==========================================================
# TEST 1: Import chain ไม่พังแล้ว
# ==========================================================

check(
    "dw_scanner import แก้แล้ว (get_scanner_data เรียกได้)",
    hasattr(dw_scanner, "get_scanner_data")
)


# ==========================================================
# TEST 2: กรองตาม underlying จริง (บั๊กเดิม)
# ==========================================================

dw_scanner.get_scanner_data = fake_get_scanner_data  # monkeypatch แทนของจริง

# สำคัญ: patch ตัว Yuanta merge ด้วย ไม่งั้นบนเครื่องที่ต่อเน็ตได้จริง
# มันจะไปดึงข้อมูลสดจาก dw19club.com มาปนกับข้อมูลปลอมด้านบน
# ทำให้ผลเทสต์ไม่นิ่ง (นี่คือสาเหตุที่เทสต์ล้ม 1 ตัวตอนรันบนเครื่องจริง)
dw_scanner.get_yuanta_dw = lambda underlying: []

ptt_call = dw_scanner.get_best_dw("PTT", "BUY")

check(
    "ขอ DW ของ PTT ได้ผลลัพธ์อย่างน้อย 1 ตัว",
    len(ptt_call) >= 1
)

check(
    "ทุกตัวที่ได้กลับมาต้องเป็น underlying = PTT เท่านั้น (ไม่มี KBANK ปน)",
    all(d["underlying"] == "PTT" for d in ptt_call)
)

check(
    "ไม่มี KBANK19C2611A ปนมาทั้งที่คุณภาพดีกว่า (นี่คือบั๊กเดิมที่แก้ไปแล้ว)",
    all(d["symbol"] != "KBANK19C2611A" for d in ptt_call)
)

check(
    "PTT01C2611A (ผ่านทุกเกณฑ์) ต้องอยู่ในผลลัพธ์",
    any(d["symbol"] == "PTT01C2611A" for d in ptt_call)
)

check(
    "PTT01C2611B (Sensitivity ต่ำกว่าเกณฑ์) ต้องถูกตัดออก",
    all(d["symbol"] != "PTT01C2611B" for d in ptt_call)
)

check(
    "PTT01P2611A (เป็น PUT ไม่ใช่ CALL) ต้องถูกตัดออกตอนขอ CALL",
    all(d["symbol"] != "PTT01P2611A" for d in ptt_call)
)

check(
    "PTT01C2611C (liquidity แย่) ต้องถูกตัดออก",
    all(d["symbol"] != "PTT01C2611C" for d in ptt_call)
)

# ขอ DW ของหุ้นที่ไม่มีข้อมูลเลย -> ต้องได้ list ว่าง ไม่ crash
none_symbol = dw_scanner.get_best_dw("SCB", "BUY")
check(
    "ขอ DW ของหุ้นที่ไม่มีข้อมูล -> ได้ list ว่าง ไม่ error",
    none_symbol == []
)


# ==========================================================
# TEST 3: format_dw_message ไม่พังหลังตัด score/hybrid ออก
# ==========================================================

msg = dw_formatter.format_dw_message(
    trend="BUY",
    symbol="PTT",
    dw=ptt_call,
    market="Bullish",
    risk="NORMAL",
    target="Momentum",
    hold="Intraday",
)

check(
    "format_dw_message คืนค่าเป็น string ไม่ว่าง",
    isinstance(msg, str) and len(msg) > 0
)

check(
    "ข้อความมี symbol ของ DW ที่ผ่าน filter อยู่จริง",
    "PTT01C2611A" in msg
)

check(
    "ข้อความไม่มี KBANK ปนมา",
    "KBANK" not in msg
)


# ==========================================================
# TEST 4: get_risk_level (Main.py) ยังจัดหมวดถูกต้อง
# ==========================================================

risk, target, hold = Main.get_risk_level(sens=1.30, delta=0.6, gearing=13)
check(
    "Gearing/Sensitivity สูงมาก -> ควรจัดเป็น HIGH risk",
    risk == "HIGH"
)

risk, target, hold = Main.get_risk_level(sens=1.05, delta=0.55, gearing=8)
check(
    "ค่ากลาง ๆ ตามเกณฑ์ -> ควรจัดเป็น NORMAL risk",
    risk == "NORMAL"
)

risk, target, hold = Main.get_risk_level(sens=0.5, delta=0.2, gearing=3)
check(
    "ค่าต่ำ -> ควรจัดเป็น LOW risk",
    risk == "LOW"
)

risk, target, hold = Main.get_risk_level(sens=0, delta=0, gearing=0, is_forex=True)
check(
    "Forex -> ควรเป็น NORMAL/Swing เสมอ ไม่เข้ากฎ DW",
    (risk, target, hold) == ("NORMAL", "Swing", "Intraday")
)


# ==========================================================
# TEST 5: yuanta_api.normalize_dw - ใช้ข้อมูลตัวอย่างจริงจาก
# dw19club.com/api/search/advance ที่ผู้ใช้ copy มาจาก DevTools
# ==========================================================

import yuanta_api

SAMPLE_YUANTA_ITEM = {
    "symbol": "SET5019C2609B",
    "type": "C",
    "price": 0.54,
    "gearing": 22,
    "sen": 1.095,
    "implied_vol": 22.71,
    "decay": 1,
    "issuer": "YUANTA",
    "exercise_price": 1210,
    "moneyness": -10.31,
    "ratio": 0.07819,
    "last_trade": "29/09/2026 00:00:00",
    "ltd": 61,
    "is_recommend": True,
    "group_no": None,
}

rec = yuanta_api.normalize_dw(SAMPLE_YUANTA_ITEM, "SET50")

check(
    "yuanta normalize_dw: symbol ตรง",
    rec["symbol"] == "SET5019C2609B"
)

check(
    "yuanta normalize_dw: type C -> CALL",
    rec["type"] == "CALL"
)

check(
    "yuanta normalize_dw: sensitivity แปลงจาก 'sen' ถูกต้อง",
    rec["sensitivity"] == 1.095
)

check(
    "yuanta normalize_dw: days_left แปลงจาก 'ltd' ถูกต้อง",
    rec["days_left"] == 61
)

check(
    "yuanta normalize_dw: มี delta ประมาณค่าให้ (ไม่ใช่ 0)",
    rec["delta"] > 0
)

check(
    "yuanta normalize_dw: underlying ติดตามที่ขอไป (SET50)",
    rec["underlying"] == "SET50"
)

check(
    "yuanta normalize_dw: ไม่ throw error เวลาข้อมูลแปลก (dict ว่าง)",
    yuanta_api.normalize_dw({}, "SET50") is None
)

check(
    "yuanta_api._extract_list หา list ของ dw เจอแม้ห่อด้วย key 'data'",
    len(yuanta_api._extract_list({"success": True, "data": [SAMPLE_YUANTA_ITEM]})) == 1
)

check(
    "yuanta_api._extract_list หา list เจอแม้ห่อซ้อน 2 ชั้น (data.list)",
    len(yuanta_api._extract_list({"data": {"list": [SAMPLE_YUANTA_ITEM, SAMPLE_YUANTA_ITEM]}})) == 2
)


# ==========================================================
# TEST 6: data_loader._download_ohlc - จำลอง error ของ Yahoo จริง
# ที่เจอกับ ^SET50.BK ("Period 'max' is invalid, must be one of: 1d, 5d")
# แล้วเช็คว่า fallback ไป start/end ทำงานถูกต้อง
# ==========================================================

import pandas as pd
import data_loader


class FakeYFError(Exception):
    pass


def make_fake_df(rows=120):
    return pd.DataFrame(
        {
            "Open": [1.0] * rows,
            "High": [1.0] * rows,
            "Low": [1.0] * rows,
            "Close": [1.0] * rows,
            "Volume": [0] * rows,
        }
    )


call_log = []


def fake_yf_download_period_max_fails(*args, **kwargs):
    call_log.append(kwargs)

    if kwargs.get("period") == "max":
        raise FakeYFError(
            "Period 'max' is invalid, must be one of: 1d, 5d"
        )

    # จำลองว่าพอใช้ start/end แทนแล้วได้ข้อมูลจริง
    return make_fake_df()


data_loader.yf.download = fake_yf_download_period_max_fails
call_log.clear()

result = data_loader._download_ohlc("^SET50.BK", "^SET50")

check(
    "_download_ohlc: period=max พังแล้ว fallback ไป start/end จนได้ข้อมูลจริง",
    result is not None and not result.empty
)

check(
    "_download_ohlc: มีการลองใช้ start/end จริง (ไม่ใช่แค่ period=max ซ้ำ ๆ)",
    any("start" in c for c in call_log)
)


def fake_yf_download_all_fail(*args, **kwargs):
    return pd.DataFrame()  # ว่างเปล่าทุกครั้ง (จำลองกรณีไม่มีข้อมูลจริง ๆ )


data_loader.yf.download = fake_yf_download_all_fail

result2 = data_loader._download_ohlc("^FAKE.BK", "FAKE")

check(
    "_download_ohlc: ถ้าทุกช่วงเวลาว่างหมดจริง ๆ ต้องคืน None ไม่ error",
    result2 is None
)


# ==========================================================
# TEST 7: get_data() ไม่ทิ้งข้อมูลเกือบทั้งหมดอีกต่อไป เมื่อ Volume
# เป็น NaN เกือบทุกแถว (เจอจริงกับ ^SET50.BK - ได้แค่ 1 แท่งจาก 120)
# ==========================================================

import numpy as np

def make_index_like_df(rows=120):
    # จำลองข้อมูล index ให้ตรงกับที่เจอจริงจาก Yahoo สำหรับ ^SET50.BK:
    # Close มีค่าครบทุกแถว แต่ Open/High/Low/Volume เป็น NaN เกือบหมด
    # (มีค่าจริงแค่ไม่กี่แถวล่าสุด) เพราะดัชนีนี้ไม่มี intraday tick
    # ย้อนหลังให้ครบเหมือนหุ้นทั่วไป
    dates = pd.date_range("2020-01-01", periods=rows, freq="D")

    base = 1000 + np.cumsum(np.random.default_rng(42).normal(0, 1, rows))

    # แถวส่วนใหญ่ไม่มี Open/High/Low/Volume จริง มีแค่ Close
    open_col = [np.nan] * (rows - 1) + [base[-1]]
    high_col = [np.nan] * (rows - 1) + [base[-1] + 1]
    low_col = [np.nan] * (rows - 1) + [base[-1] - 1]
    volume = [np.nan] * (rows - 1) + [0.0]

    return pd.DataFrame(
        {
            "Open": open_col,
            "High": high_col,
            "Low": low_col,
            "Close": base,
            "Volume": volume,
        },
        index=dates,
    )


def fake_yf_download_index_like(*args, **kwargs):
    if kwargs.get("period") == "max":
        raise FakeYFError(
            "Period 'max' is invalid, must be one of: 1d, 5d"
        )

    return make_index_like_df()


data_loader.yf.download = fake_yf_download_index_like
data_loader.price_cache_test = {}

set50_result = data_loader.get_data("^SET50", True, {})

check(
    "get_data(^SET50): ไม่ crash และคืนค่า DataFrame จริง",
    set50_result is not None
)

check(
    "get_data(^SET50): ไม่ทิ้งข้อมูลจนเหลือแค่ 1-2 แถว (บั๊กเดิม dropna() ทิ้งเพราะ Volume เป็น NaN)",
    set50_result is not None and len(set50_result) >= 50
)

check(
    "get_data(^SET50): คอลัมน์ Volume ไม่มี NaN หลงเหลือ",
    set50_result is not None and not set50_result["Volume"].isna().any()
)

check(
    "get_data(^SET50): Open/High/Low ไม่มี NaN หลงเหลือ (เติมจาก Close แล้ว)",
    set50_result is not None
    and not set50_result[["Open", "High", "Low"]].isna().any().any()
)


# ==========================================================
# TEST 8: ^SET50 ต้องใช้ ticker TDEX.BK (ETF) แทน ^SET50.BK (ดัชนีดิบ)
# เพราะ ^SET50.BK ยืนยันแล้วว่า yfinance ดึงได้แค่ 1 แท่งเท่านั้น
# ไม่ว่าจะพยายามแก้ด้วยวิธีไหนก็ตาม ส่วน TDEX.BK เป็น ETF ที่เทรดจริง
# มี OHLCV ปกติสมบูรณ์
# ==========================================================

requested_tickers = []


def fake_yf_download_record_ticker(ticker, *args, **kwargs):
    requested_tickers.append(ticker)
    return make_index_like_df(rows=10)  # แค่เช็ค ticker ที่ขอ ไม่ได้เช็คเนื้อข้อมูล


data_loader.yf.download = fake_yf_download_record_ticker
requested_tickers.clear()

data_loader.get_data("^SET50", True, {})

check(
    "^SET50 เรียก yfinance ด้วย ticker 'TDEX.BK' (ไม่ใช่ '^SET50.BK' ที่มีปัญหา)",
    "TDEX.BK" in requested_tickers
)

check(
    "^SET50 ไม่เรียก '^SET50.BK' อีกต่อไป",
    "^SET50.BK" not in requested_tickers
)


# ==========================================================
# SUMMARY
# ==========================================================

print()
print(f"สรุปผล: PASS {PASS} / FAIL {FAIL}")

if FAIL > 0:
    sys.exit(1)
