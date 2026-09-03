# ==========================================================
# DW MESSAGE FORMATTER (COMPACT)
# ปรับให้สั้นกระชับ ตัด emoji/กรอบเส้นออก
# เพิ่มบรรทัดแจ้ง volume ผิดปกติ (แสดงเฉพาะตอนที่ผิดปกติจริง)
# ==========================================================

def format_dw_message(
    trend,
    symbol,
    dw,
    market,
    score=None,
    volume_spike=False,
    price_action=None,
    fibo=None,
    risk="NORMAL",
    target="Standard",
    hold="Intraday",
    quality="B",
    reasons=None
):
    if trend in ["BUY", "BULLISH"]:
        signal_text = "BUY"
    elif trend in ["SELL", "BEARISH"]:
        signal_text = "SELL"
    else:
        signal_text = "WAIT"

    # ---- หัวข้อ: SYMBOL SIGNAL (SCORE) ----
    head = f"{symbol} {signal_text}"
    if score is not None:
        head += f" ({score})"
    lines = [head]

    # ---- แจ้งเฉพาะตอน volume ผิดปกติ ----
    if volume_spike:
        lines.append("Volume ผิดปกติ (สูงกว่าเฉลี่ย 20 วัน)")

    # ---- บรรทัดสรุป market/risk/hold รวมบรรทัดเดียว ----
    lines.append(f"{market} | {risk} | {hold}")

    # ---- DW candidates (เอาแค่ตัวท็อป 1-2 ตัว แบบบรรทัดเดียว) ----
    if isinstance(dw, dict):
        dw = [dw]

    if isinstance(dw, list) and len(dw) > 0:
        for item in dw[:2]:
            lines.append(
                f"DW {item.get('symbol', '-')} "
                f"{item.get('issuer', '-')} "
                f"Sens{item.get('sensitivity', '-')} "
                f"D{item.get('delta', '-')} "
                f"Gear{item.get('effective_gearing', '-')}x"
            )
    else:
        lines.append("ไม่มี DW ผ่าน Filter")

    return "\n".join(lines)
