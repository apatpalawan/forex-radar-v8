# ==========================================================
# VOLUME ANOMALY SCANNER V1.0
#
# ตรวจจับหุ้นไทยที่มี Volume เข้าผิดปกติ (Volume Spike)
# เทียบกับค่าเฉลี่ย 20 วัน (VOL_MA20 ที่คำนวณไว้แล้วใน indicator.py)
#
# เมื่อพบ Volume ผิดปกติ -> ใช้ทิศทางแท่งเทียนของวันนั้น
# (Close vs Open) กำหนดทิศทาง BUY/SELL แล้วส่งต่อให้
# dw_scanner.py หา DW ที่เหมาะสม (เน้น sensitivity ใกล้ 1
# หรือมากกว่า ผ่าน parameter min_sensitivity ที่เพิ่มเข้าไปใน
# get_best_dw())
#
# ทำงานเป็นระบบแยกอิสระจาก signal_engine.py (EMA Trend/Score)
# เดิม ไม่ไปแตะ/เปลี่ยนพฤติกรรมของ pipeline เดิม
# ==========================================================

import logging

from config import ABNORMAL_VOLUME_RATIO


def detect_abnormal_volume(symbol, df):
    """
    ตรวจสอบว่าแท่งล่าสุดของ df มี Volume ผิดปกติหรือไม่

    เงื่อนไข "ผิดปกติ":
    Volume แท่งล่าสุด >= ABNORMAL_VOLUME_RATIO เท่าของ VOL_MA20
    (ค่าเฉลี่ย Volume ย้อนหลัง 20 วัน จาก indicator.py)

    คืนค่า:
    dict {symbol, direction, ratio, volume, vol_ma20, close, open}
    ถ้าพบความผิดปกติ มิฉะนั้นคืนค่า None
    """
    if df is None or df.empty:
        return None

    required = ["Close", "Open", "Volume", "VOL_MA20"]
    for col in required:
        if col not in df.columns:
            logging.warning(
                f"{symbol} VOLUME SCAN SKIP : MISSING COLUMN {col}"
            )
            return None

    last = df.iloc[-1]

    try:
        vol_ma20 = float(last.get("VOL_MA20", 0) or 0)
        volume = float(last.get("Volume", 0) or 0)
        close = float(last.get("Close", 0) or 0)
        open_ = float(last.get("Open", close) or close)
    except (TypeError, ValueError):
        return None

    # ป้องกัน MA20 เป็น 0/NaN (แถวต้น ๆ ของข้อมูลที่ยังไม่ครบ 20 วัน)
    if vol_ma20 <= 0:
        return None

    ratio = volume / vol_ma20

    if ratio < ABNORMAL_VOLUME_RATIO:
        return None

    # ทิศทางจากแท่งเทียนที่ Volume ผิดปกติ:
    # ปิดสูงกว่าหรือเท่ากับเปิด = แรงซื้อเข้า (BUY -> หา DW CALL)
    # ปิดต่ำกว่าเปิด = แรงขายออก (SELL -> หา DW PUT)
    direction = "BUY" if close >= open_ else "SELL"

    logging.info(
        f"{symbol} VOLUME ABNORMAL : "
        f"x{ratio:.2f} (Vol={volume:.0f} / MA20={vol_ma20:.0f}) "
        f"DIR={direction}"
    )

    return {
        "symbol": symbol,
        "direction": direction,
        "ratio": ratio,
        "volume": volume,
        "vol_ma20": vol_ma20,
        "close": close,
        "open": open_,
    }
