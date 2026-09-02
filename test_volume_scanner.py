# ==========================================================
# TEST: volume_scanner.py
# รันแบบ offline ล้วน ๆ ไม่ต้องต่อ internet / yfinance จริง
# ตาม README เดิม: "ห้ามรันจริงก่อนเทสต์ผ่าน"
#
# วิธีรัน:
#   python test_volume_scanner.py
# ==========================================================

import pandas as pd
import numpy as np

from volume_scanner import detect_abnormal_volume

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


def make_df(volumes, closes, opens=None):
    n = len(volumes)
    if opens is None:
        opens = closes
    df = pd.DataFrame(
        {
            "Open": opens,
            "Close": closes,
            "Volume": volumes,
        }
    )
    df["VOL_MA20"] = df["Volume"].rolling(20).mean()
    return df


# ----------------------------------------------------------
# CASE 1: Volume ปกติ (ไม่ควรเจอความผิดปกติ)
# ----------------------------------------------------------
volumes = [1_000_000] * 25
closes = [10.0] * 25
df_normal = make_df(volumes, closes)
result = detect_abnormal_volume("TEST1", df_normal)
check("Case1 - normal volume -> None", result is None)

# ----------------------------------------------------------
# CASE 2: Volume แท่งล่าสุดพุ่ง 3 เท่า + ปิดสูงกว่าเปิด -> BUY
# ----------------------------------------------------------
volumes = [1_000_000] * 24 + [3_000_000]
closes = [10.0] * 24 + [10.5]
opens = [10.0] * 24 + [10.0]
df_spike_buy = make_df(volumes, closes, opens)
result = detect_abnormal_volume("TEST2", df_spike_buy)
check("Case2 - volume spike found", result is not None)
if result:
    check("Case2 - direction BUY", result["direction"] == "BUY")
    # หมายเหตุ: VOL_MA20 เป็น rolling(20) ซึ่งรวมแท่งล่าสุดที่ volume พุ่งด้วย
    # ดังนั้นค่าเฉลี่ยจะถูกดึงขึ้นเล็กน้อย -> ratio จริงจะน้อยกว่า 3.0 นิดหน่อย
    # (19 แท่ง x 1,000,000 + 1 แท่ง x 3,000,000) / 20 = 1,100,000
    # ratio = 3,000,000 / 1,100,000 = 2.727
    check(
        "Case2 - ratio ~= 2.727 (MA20 includes spike bar)",
        abs(result["ratio"] - 2.727) < 0.01,
    )

# ----------------------------------------------------------
# CASE 3: Volume พุ่ง 4 เท่า + ปิดต่ำกว่าเปิด -> SELL
# ----------------------------------------------------------
volumes = [1_000_000] * 24 + [4_000_000]
closes = [10.0] * 24 + [9.4]
opens = [10.0] * 24 + [10.0]
df_spike_sell = make_df(volumes, closes, opens)
result = detect_abnormal_volume("TEST3", df_spike_sell)
check("Case3 - volume spike found", result is not None)
if result:
    check("Case3 - direction SELL", result["direction"] == "SELL")

# ----------------------------------------------------------
# CASE 4: Volume พุ่งแค่ 1.3 เท่า (ต่ำกว่าเกณฑ์ default 2.0) -> None
# ----------------------------------------------------------
volumes = [1_000_000] * 24 + [1_300_000]
closes = [10.0] * 24 + [10.2]
df_below_threshold = make_df(volumes, closes)
result = detect_abnormal_volume("TEST4", df_below_threshold)
check("Case4 - below threshold -> None", result is None)

# ----------------------------------------------------------
# CASE 5: ข้อมูลไม่ครบคอลัมน์ (ไม่มี VOL_MA20) -> None ไม่ crash
# ----------------------------------------------------------
df_missing_col = pd.DataFrame(
    {
        "Open": [10.0],
        "Close": [10.0],
        "Volume": [1_000_000],
    }
)
result = detect_abnormal_volume("TEST5", df_missing_col)
check("Case5 - missing column -> None (no crash)", result is None)

# ----------------------------------------------------------
# CASE 6: df ว่างเปล่า / None -> None ไม่ crash
# ----------------------------------------------------------
check("Case6a - empty df -> None", detect_abnormal_volume("TEST6", pd.DataFrame()) is None)
check("Case6b - None df -> None", detect_abnormal_volume("TEST6", None) is None)

print()
print("=" * 40)
print(f"RESULT: PASS {PASS} / FAIL {FAIL}")
print("=" * 40)

if FAIL > 0:
    raise SystemExit(1)
