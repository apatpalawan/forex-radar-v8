import os
import time
import logging
import requests

try:
    from config import LINE_CHANNEL_ACCESS_TOKEN
except Exception:
    LINE_CHANNEL_ACCESS_TOKEN = None


# ==========================================
# LINE API
# ==========================================

LINE_URL = (
    "https://api.line.me/v2/bot/message/push"
)


# ==========================================
# TOKEN
# ==========================================

CHANNEL_ACCESS_TOKEN = (
    os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    or LINE_CHANNEL_ACCESS_TOKEN
)


LINE_USER_ID = os.getenv(
    "LINE_USER_ID"
)


# ==========================================
# FIX (Aug 2026): LINE ตอบ 400 "Length must be
# between 0 and 5000" ทั้งที่โค้ดเดิม truncate ด้วย
# str(message)[:5000] ไปแล้ว
#
# สาเหตุจริง: ข้อความมีอีโมจิเยอะ (📊🔥🎯 ฯลฯ) ซึ่งเป็น
# Unicode supplementary plane (U+10000 ขึ้นไป) - ฝั่ง LINE
# นับความยาวแบบ UTF-16 code unit (เหมือน JS string.length)
# ทำให้อีโมจิ 1 ตัว = 2 หน่วย แต่ Python len()/slice นับเป็น
# 1 code point เท่ากับ 1 หน่วยเสมอ พอข้อความมีอีโมจิเยอะ
# ความยาวจริงฝั่ง LINE เลยเกิน 5000 ทั้งที่ Python นับได้ <=5000
#
# วิธีแก้: คำนวณความยาวแบบ UTF-16 จริง + แบ่งข้อความเป็น
# หลายก้อนตามขอบเขตข้อความ (ไม่ตัดกลางข้อความ) แทนการ
# truncate ทิ้งดื้อ ๆ ซึ่งจะทำให้เนื้อหาขาดหาย
# ==========================================

MAX_UTF16_LEN = 4800  # เผื่อ margin จาก limit จริง 5000
MAX_MESSAGES_PER_PUSH = 5  # ข้อจำกัดของ LINE push API ต่อ 1 request


def _utf16_len(text):
    # นับความยาวแบบเดียวกับที่ LINE ใช้ตรวจสอบจริง
    # (UTF-16 code unit: astral char เช่นอีโมจิ = 2 หน่วย)
    return len(text.encode("utf-16-le")) // 2


def _hard_truncate_utf16(text, max_len):
    # ใช้เฉพาะกรณี "ข้อความก้อนเดียวยาวเกิน max_len เอง"
    # (ปกติไม่ควรเกิดถ้า dw_formatter คุมความยาวดี) ตัดแบบ
    # ปลอดภัยไม่ตัดกลาง surrogate pair
    encoded = text.encode("utf-16-le")
    cut = encoded[: max_len * 2]
    # เผื่อ cut ตรงกลาง surrogate pair (2 bytes ไม่ครบคู่)
    return cut.decode("utf-16-le", errors="ignore")


def _split_into_chunks(parts, max_len=MAX_UTF16_LEN):
    # parts: list ของข้อความย่อย (แต่ละ signal 1 ก้อน)
    # รวมกันเป็น chunk โดยไม่ให้ chunk ไหนเกิน max_len
    # และไม่ตัดกลางเนื้อหาของ part ใด ๆ (ยกเว้น part เดียว
    # ที่ยาวเกิน max_len เอง ถึงจะตัดแบบปลอดภัย)
    chunks = []
    current = []
    current_len = 0

    for part in parts:
        part = str(part)
        part_len = _utf16_len(part)

        if part_len > max_len:
            part = _hard_truncate_utf16(part, max_len)
            part_len = _utf16_len(part)

        sep_len = 2 if current else 0  # "\n\n"

        if current and (current_len + sep_len + part_len) > max_len:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
            sep_len = 0

        current.append(part)
        current_len += sep_len + part_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


# ==========================================
# SEND LINE
# ==========================================

def send_line(message):
    # message: str เดี่ยว หรือ list[str] (ถ้าเป็น list จะแบ่ง
    # เป็นหลาย message ให้อัตโนมัติตามความยาว UTF-16 จริง)

    if not CHANNEL_ACCESS_TOKEN:

        logging.error(
            "LINE TOKEN NOT FOUND"
        )

        return False


    if not LINE_USER_ID:

        logging.error(
            "LINE USER ID NOT FOUND"
        )

        return False


    if not message:

        logging.warning(
            "EMPTY MESSAGE"
        )

        return False


    parts = message if isinstance(message, list) else [message]
    parts = [str(p) for p in parts if str(p).strip()]

    if not parts:
        logging.warning(
            "EMPTY MESSAGE"
        )
        return False

    chunks = _split_into_chunks(parts)

    headers = {

        "Authorization":
            f"Bearer {CHANNEL_ACCESS_TOKEN}",

        "Content-Type":
            "application/json"

    }

    all_ok = True

    # LINE push API รับ messages array ได้สูงสุด 5 ต่อ 1 request
    # ถ้า chunk เกิน 5 ให้แบ่งยิงหลาย request
    for i in range(0, len(chunks), MAX_MESSAGES_PER_PUSH):

        batch = chunks[i:i + MAX_MESSAGES_PER_PUSH]

        payload = {

            "to":
                LINE_USER_ID,

            "messages": [
                {
                    "type": "text",
                    "text": text,
                }
                for text in batch
            ]

        }

        sent = False

        for attempt in range(3):

            try:

                response = requests.post(
                    LINE_URL,
                    headers=headers,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:

                    logging.info(
                        f"LINE SEND SUCCESS (batch {i // MAX_MESSAGES_PER_PUSH + 1}, "
                        f"{len(batch)} message(s))"
                    )

                    sent = True
                    break

                else:

                    logging.error(
                        f"LINE ERROR "
                        f"{response.status_code} "
                        f"{response.text}"
                    )

            except requests.exceptions.Timeout:

                logging.warning(
                    f"LINE TIMEOUT "
                    f"{attempt+1}/3"
                )

            except Exception as e:

                logging.error(
                    f"LINE ERROR : {e}"
                )

            time.sleep(2)

        if not sent:
            logging.error(
                f"LINE SEND FAILED (batch {i // MAX_MESSAGES_PER_PUSH + 1})"
            )
            all_ok = False

    return all_ok
