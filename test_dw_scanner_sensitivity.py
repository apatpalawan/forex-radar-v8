# ==========================================================
# TEST: dw_scanner.py (min_sensitivity parameter)
# รันแบบ offline - ใช้ dw dict จำลอง ไม่เรียก BLS/Yuanta จริง
# (bls_api.py ในโฟลเดอร์นี้เป็น STUB สำหรับทดสอบเท่านั้น)
#
# วิธีรัน:
#   python test_dw_scanner_sensitivity.py
# ==========================================================

from dw_scanner import pass_filter, MIN_SENSITIVITY

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


def make_dw(sensitivity, dw_type="CALL", issuer="BLS", delta=0.5,
            gearing=8, days_left=45, spread=0.01, liquidity="NORMAL"):
    return {
        "symbol": "TEST19C2609A",
        "type": dw_type,
        "issuer": issuer,
        "sensitivity": sensitivity,
        "delta": delta,
        "effective_gearing": gearing,
        "days_left": days_left,
        "spread": spread,
        "liquidity": liquidity,
    }


# ----------------------------------------------------------
# CASE 1: ไม่ส่ง min_sensitivity -> ใช้ค่า default เดิม (0.95)
# ----------------------------------------------------------
dw_096 = make_dw(sensitivity=0.96)
check(
    "Case1 - no min_sensitivity, sens=0.96 passes default 0.95",
    pass_filter(dw_096, "BUY") is True,
)

dw_090 = make_dw(sensitivity=0.90)
check(
    "Case1b - no min_sensitivity, sens=0.90 fails default 0.95",
    pass_filter(dw_090, "BUY") is False,
)

# ----------------------------------------------------------
# CASE 2: ส่ง min_sensitivity=1.0 (ตามที่ผู้ใช้ขอ "ใกล้ 1 หรือเกิน")
# ----------------------------------------------------------
dw_105 = make_dw(sensitivity=1.05)
check(
    "Case2 - min_sensitivity=1.0, sens=1.05 passes",
    pass_filter(dw_105, "BUY", min_sensitivity=1.0) is True,
)

dw_098 = make_dw(sensitivity=0.98)
check(
    "Case2b - min_sensitivity=1.0, sens=0.98 fails (below 1.0)",
    pass_filter(dw_098, "BUY", min_sensitivity=1.0) is False,
)

# ----------------------------------------------------------
# CASE 3: fallback min_sensitivity=0.95 (DW_FALLBACK_SENSITIVITY)
# sens=0.98 ควรผ่านเมื่อผ่อนเกณฑ์ลงมาที่ 0.95
# ----------------------------------------------------------
check(
    "Case3 - min_sensitivity=0.95 (fallback), sens=0.98 passes",
    pass_filter(dw_098, "BUY", min_sensitivity=0.95) is True,
)

# ----------------------------------------------------------
# CASE 4: ทิศทางไม่ตรง (PUT ตอนต้องการ BUY) -> fail เหมือนเดิม
# ไม่ว่าจะ sensitivity เท่าไหร่
# ----------------------------------------------------------
dw_put = make_dw(sensitivity=1.20, dw_type="PUT")
check(
    "Case4 - wrong direction fails regardless of sensitivity",
    pass_filter(dw_put, "BUY", min_sensitivity=1.0) is False,
)

print()
print(f"MIN_SENSITIVITY module default = {MIN_SENSITIVITY}")
print("=" * 40)
print(f"RESULT: PASS {PASS} / FAIL {FAIL}")
print("=" * 40)

if FAIL > 0:
    raise SystemExit(1)
