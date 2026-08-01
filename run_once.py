# ==========================================================
# RUN ONCE - สำหรับ GitHub Actions (หรือ cron/scheduler อื่น)
#
# ต่างจาก Main.py ตรงที่:
# - ไม่มี while True / time.sleep เลย -> สแกน 1 รอบแล้วจบโปรแกรม
# - ไม่เช็ค is_send_time() -> ส่งเสมอทุกครั้งที่ถูกเรียก เพราะตัวจับ
#   เวลาข้างนอก (GitHub Actions cron) เป็นคนคุมว่าจะเรียกตอนไหนแทน
#
# วิธีรัน:
#   python run_once.py
# ==========================================================

import logging
import sys

import Main


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def main():
    logging.info(
        f"Forex Radar V{Main.VERSION} - RUN ONCE START"
    )

    try:
        sent = Main.run_scan_cycle(force_send=True)

        logging.info(
            f"RUN ONCE DONE (ส่ง LINE: {sent})"
        )

        return 0

    except Exception as e:
        logging.exception(
            f"RUN ONCE FAILED: {e}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
