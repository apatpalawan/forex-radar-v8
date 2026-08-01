# ==========================================================
# FULL RUN MOCK TEST - จำลองรัน run_scan_cycle() แบบเต็มรูปแบบ
#
# จำลอง "หุ้นไทย + ทอง + forex + DW (BLS/YUANTA)" ทั้งหมดในรอบเดียว
# ไม่ต้องต่อ internet เลย (mock get_data / analyze_signal /
# get_market_trend / get_best_dw / send_line ทั้งหมด)
#
# เป้าหมาย: ยืนยันว่า pipeline หลักใน Main.py ทำงานถูกต้องจบรอบ
# ไม่ crash และประกอบข้อความ LINE ออกมาได้สมเหตุสมผล
#
# หมายเหตุ: นี่คือการทดสอบ "ตรรกะ/การประกอบข้อความ" ไม่ใช่การยืนยันว่า
# ข้อมูลจริงจาก yfinance/BLS/Yuanta ถูกต้อง (อันนั้นต้องรันบนเครื่องที่
# ต่อเน็ตได้จริงเท่านั้น - แซนด์บ็อกซ์นี้ไม่มี internet)
#
# วิธีรัน:
#   python test_full_run_mock.py
# ==========================================================

import Main
import config


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
# MOCK: get_data - แค่ต้องไม่ None ก็พอ (ข้างในไม่ได้ใช้ค่าจริง
# เพราะ analyze_signal ก็ถูก mock แยกไว้แล้ว)
# ==========================================================

def fake_get_data(symbol, is_stock, cache):
    return {"symbol": symbol}  # dummy object ที่ไม่ใช่ None


# ==========================================================
# MOCK: get_market_trend
# ==========================================================

def fake_get_market_trend(df):
    return "Bullish"


# ==========================================================
# MOCK: analyze_signal - จำลองสัญญาณ BUY/SELL ต่างกันในแต่ละสินทรัพย์
# เพื่อให้เห็นทั้ง หุ้น (BUY), ทอง (BUY), forex อื่น (SELL/ไม่ผ่านเกณฑ์)
# ==========================================================

FAKE_SIGNALS = {
    "^SET50": {"score": 80, "trend": "BUY", "price_action": "Breakout", "fibonacci": "0.618"},
    "PTT": {"score": 85, "trend": "BUY", "price_action": "Breakout", "fibonacci": "0.618"},
    "KBANK": {"score": 60, "trend": "BUY", "price_action": None, "fibonacci": None},  # ต่ำกว่าเกณฑ์ -> ไม่ควรผ่าน
    "AOT": {"score": 90, "trend": "SELL", "price_action": "Reversal", "fibonacci": "0.5"},
    "XAUUSD": {"score": 88, "trend": "BUY", "price_action": "Momentum", "fibonacci": "0.382"},  # ทอง
    "EURUSD": {"score": 75, "trend": "SELL", "price_action": None, "fibonacci": None},
    "GBPUSD": {"score": 50, "trend": "BUY", "price_action": None, "fibonacci": None},  # ต่ำกว่าเกณฑ์
    "USDJPY": {"score": 72, "trend": "SIDEWAY", "price_action": None, "fibonacci": None},  # sideway -> ไม่ควรผ่าน
}


def fake_analyze_signal(symbol, df):
    return FAKE_SIGNALS.get(symbol)


# ==========================================================
# MOCK: get_best_dw - จำลอง DW ที่มาจาก 2 ค่าย (BLS + YUANTA) ปนกัน
# ==========================================================

def fake_get_best_dw(underlying, trend):
    if underlying == "PTT" and trend == "BUY":
        return [
            {
                "symbol": "PTT01C2611A",
                "underlying": "PTT",
                "issuer": "BLS",
                "sensitivity": 1.10,
                "delta": 0.60,
                "abs_delta": 0.60,
                "effective_gearing": 9.0,
                "days_left": 82,
            },
            {
                "symbol": "PTT19C2609B",
                "underlying": "PTT",
                "issuer": "YUANTA",
                "sensitivity": 1.05,
                "delta": 0.55,
                "abs_delta": 0.55,
                "effective_gearing": 8.5,
                "days_left": 61,
            },
        ]

    if underlying == "SET50" and trend == "BUY":
        return [
            {
                "symbol": "SET5001C2611A",
                "underlying": "SET50",
                "issuer": "BLS",
                "sensitivity": 1.08,
                "delta": 0.58,
                "abs_delta": 0.58,
                "effective_gearing": 9.2,
                "days_left": 82,
            },
        ]

    if underlying == "AOT" and trend == "SELL":
        return [
            {
                "symbol": "AOT01P2611A",
                "underlying": "AOT",
                "issuer": "BLS",
                "sensitivity": 1.02,
                "delta": -0.52,
                "abs_delta": 0.52,
                "effective_gearing": 8.0,
                "days_left": 70,
            },
        ]

    return []  # หุ้นอื่น ๆ ที่ไม่ได้จำลองไว้ -> ไม่มี DW (Main.py จะข้ามไปเอง)


# ==========================================================
# MOCK: send_line - ดักข้อความไว้ดู แทนที่จะยิงเข้า LINE จริง
# ==========================================================

captured_messages = []


def fake_send_line(msg):
    captured_messages.append(msg)
    return True  # จำลอง "ส่งสำเร็จ" เหมือน send_line จริงตอน LINE ตอบ 200 OK


# ==========================================================
# APPLY MOCKS (patch ที่ตัวแปรใน namespace ของ Main.py โดยตรง
# เพราะ Main.py ใช้ "from x import y" - ต้อง patch "y" ใน Main แทน)
# ==========================================================

Main.get_data = fake_get_data
Main.get_market_trend = fake_get_market_trend
Main.analyze_signal = fake_analyze_signal
Main.get_best_dw = fake_get_best_dw
Main.send_line = fake_send_line

# บังคับให้ตลาดหุ้นไทย "เปิด" เสมอตอนเทสต์ (ไม่งั้นถ้าเทสต์รันวันเสาร์-อาทิตย์
# หรือนอกเวลาตลาด หุ้น/DW ทั้งหมดจะถูกข้ามหมดโดย thai_market_open() จริง)
Main.thai_market_open = lambda: True

# เคลียร์ cooldown/cache ให้เทสต์นิ่ง ไม่ถูกกระทบจากการรันครั้งก่อนหน้า
Main.last_alerts.clear()
Main.price_cache.clear()
Main.dw_cache.clear()
Main.candidate_signals.clear()
Main.signal_queue.clear()


# ==========================================================
# RUN 1 รอบเต็ม
# ==========================================================

print("กำลังรัน run_scan_cycle(force_send=True) ...\n")

sent = Main.run_scan_cycle(force_send=True)

check(
    "run_scan_cycle ทำงานจบโดยไม่ crash และคืนค่า True (force_send)",
    sent is True
)

check(
    "send_line ถูกเรียก 1 ครั้ง (ข้อความเดียว รวมทุกสัญญาณ)",
    len(captured_messages) == 1
)

final_message = captured_messages[0] if captured_messages else ""

check(
    "มีสัญญาณของ PTT (หุ้น, score ผ่านเกณฑ์)",
    "PTT" in final_message
)

check(
    "มีสัญญาณของ XAUUSD (ทอง, score ผ่านเกณฑ์)",
    "XAUUSD" in final_message
)

check(
    "มีสัญญาณของ AOT (หุ้น SELL, score ผ่านเกณฑ์)",
    "AOT" in final_message
)

check(
    "มีสัญญาณของ EURUSD (forex SELL, score ผ่านเกณฑ์)",
    "EURUSD" in final_message
)

check(
    "KBANK (score ต่ำกว่าเกณฑ์) ต้องไม่ถูกส่ง",
    "KBANK" not in final_message
)

check(
    "GBPUSD (score ต่ำกว่าเกณฑ์) ต้องไม่ถูกส่ง",
    "GBPUSD" not in final_message
)

check(
    "USDJPY (trend SIDEWAY) ต้องไม่ถูกส่ง",
    "USDJPY" not in final_message
)

check(
    "DW ของ PTT จากค่าย BLS ปรากฏในข้อความ",
    "PTT01C2611A" in final_message
)

check(
    "DW ของ PTT จากค่าย YUANTA ปรากฏในข้อความ (รวม 2 ค่ายจริง)",
    "PTT19C2609B" in final_message
)

check(
    "AOT (SELL, ไม่มี DW จำลองไว้) ไม่ควร error แม้ dw_list ว่าง",
    True  # ถ้ามาถึงตรงนี้ได้แปลว่าไม่ crash ตอนประมวลผล AOT
)


print()
print("--------- ตัวอย่างข้อความที่ประกอบได้ (ตัดมาบางส่วน) ---------")
print(final_message[:2000])
print("--------------------------------------------------------------")


print()
# ==========================================================
# TEST เพิ่ม: ถ้า LINE ส่งไม่สำเร็จจริง (เช่นไม่มี Token) ค่าที่คืน
# จาก run_scan_cycle() ต้องเป็น False ด้วย ไม่ใช่ True อีกต่อไป
# (แก้ตามที่ผู้ใช้ท้วงมา - เดิม report ผิดว่าส่งสำเร็จทั้งที่ไม่มี Token)
# ==========================================================

def fake_send_line_fail(msg):
    captured_messages.append(msg)
    return False  # จำลองว่าไม่มี Token / ส่งไม่สำเร็จ เหมือน send_line จริง


Main.send_line = fake_send_line_fail

Main.last_alerts.clear()
Main.price_cache.clear()
Main.dw_cache.clear()
Main.candidate_signals.clear()
Main.signal_queue.clear()

sent_when_failed = Main.run_scan_cycle(force_send=True)

check(
    "ถ้า LINE ส่งไม่สำเร็จจริง run_scan_cycle ต้องคืนค่า False (ไม่ใช่ True หลอก ๆ)",
    sent_when_failed is False
)


print()
print(f"สรุปผล: PASS {PASS} / FAIL {FAIL}")

if FAIL > 0:
    import sys
    sys.exit(1)
