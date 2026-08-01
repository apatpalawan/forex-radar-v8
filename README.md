# Forex Radar V9 - โฟลเดอร์สำหรับทดสอบใน VSCode

โฟลเดอร์นี้มีเฉพาะไฟล์ที่ **`Main.py` ต้องใช้จริง** เท่านั้น (ไล่ตาม import ทั้งหมดแล้ว)
ไฟล์ debug/experiment เก่า (`bls_client.py`, `set_html.txt`, `highcharts_dw.js` ฯลฯ) ถูกตัดออก
เพื่อไม่ให้สับสน — ถ้าต้องการไฟล์เหล่านั้นกลับมา บอกได้เลย

## วิธีติดตั้ง (ครั้งแรกครั้งเดียว)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

## วิธีทดสอบโดยไม่ต้องต่อ internet จริง (ทำก่อนรันจริงเสมอ)

```bash
python test_pipeline_offline.py
python test_full_run_mock.py
```

- `test_pipeline_offline.py` (PASS 25/25) — เทสต์เฉพาะจุด: dw_scanner filter, underlying match, format_dw_message, get_risk_level, yuanta_api normalize
- `test_full_run_mock.py` (PASS 12/12) — เทสต์ทั้ง cycle เต็มรูปแบบ (mock หุ้น+ทอง+forex+DW 2 ค่าย) ยืนยันว่า `run_scan_cycle()` ทำงานจบไม่ crash และประกอบข้อความ LINE ถูกต้อง

ถ้ามี FAIL ในไฟล์ไหน ให้ส่ง error กลับมาดูก่อน **ห้ามรันจริง**

หมายเหตุ: บนเครื่องของคุณที่ลง `yfinance` จริงตาม `requirements.txt` แล้ว จะไม่มี error
เรื่อง yfinance เหมือนตอนที่ผมรันในนี้ (ในนี้ไม่มี internet เลยต้องใช้ stub ปลอมแทน)

**ข้อจำกัดของเทสต์ทั้ง 2 ไฟล์:** เป็นการเทสต์ "ตรรกะ/การประกอบข้อความ" เท่านั้น
ไม่ได้ยืนยันว่าข้อมูลจริงจาก yfinance/BLS/Yuanta ถูกต้อง เพราะแซนด์บ็อกซ์นี้ไม่มี
internet เลย — อันนั้นต้องรันจริงบนเครื่องคุณ (ดูหัวข้อ "วิธีรันจริง" ด้านล่าง)

## วิธีรันจริง (ต่อเนื่องบนเครื่อง/เซิร์ฟเวอร์ที่เปิดค้างได้)

```bash
python Main.py
```

จะเริ่ม loop สแกนทุก 60 วินาที และส่งเข้า LINE OA ตามเวลาที่ตั้งไว้ใน `config.py` (`SEND_TIMES`)
ต้องตั้งค่า LINE Channel Access Token / User ID ให้ `line_notify.py` อ่านได้ก่อน (ผ่าน environment
variable `LINE_CHANNEL_ACCESS_TOKEN` และ `LINE_USER_ID`)

## วิธีรันแบบครั้งเดียวจบ (สำหรับ GitHub Actions / cron)

```bash
python run_once.py
```

สแกน 1 รอบ ส่ง LINE ทันที (ไม่เช็คเวลา ไม่มี loop) แล้วจบโปรแกรม — ใช้ไฟล์
`.github/workflows/forex-radar.yml` ที่แนบมาได้เลย ตั้งเวลาไว้ 09:10 / 14:00 / 15:30
(Asia/Bangkok, จันทร์-ศุกร์) ตรงกับ `SEND_TIMES` เดิม

**ก่อนใช้งานบน GitHub ต้องตั้งค่า 2 อย่าง:**
1. Push โค้ดทั้งโฟลเดอร์นี้ขึ้น GitHub repo (private ก็ได้)
2. ไปที่ repo → Settings → Secrets and variables → Actions → New repository secret
   เพิ่ม `LINE_CHANNEL_ACCESS_TOKEN` และ `LINE_USER_ID` ให้ตรงกับที่ใช้จริง

ทดสอบได้ทันทีโดยไม่ต้องรอถึงเวลา: ไปที่แท็บ **Actions** ของ repo → เลือก workflow
"Forex Radar - Scheduled Run" → กด **Run workflow** (ปุ่มนี้มาจาก `workflow_dispatch` ในไฟล์ yml)

## ไฟล์ที่แก้/เพิ่มใหม่ในรอบนี้

| ไฟล์ | สถานะ | รายละเอียด |
|---|---|---|
| `data_loader.py` / `config.py` | แก้ (สำคัญสุด) | `^SET50.BK` (ดัชนีดิบ) ยืนยันแล้วว่า yfinance ดึงได้แค่ 1 แท่งเสมอ ไม่ว่าจะใช้ `period="max"` หรือ `start=`/`end=` แบบไหนก็ตาม (ข้อจำกัดจาก Yahoo เอง ไม่ใช่บั๊กโค้ด) เปลี่ยนไปใช้ **`TDEX.BK`** (ThaiDEX SET50 ETF ที่ไล่ตามดัชนีนี้แบบ 1:1 และเทรดจริงบนตลาด) แทน ได้ OHLCV ปกติสมบูรณ์เหมือนหุ้นทั่วไป |
| `data_loader.py` | แก้ (สำรอง/เผื่อ ticker อื่นเจอปัญหาแบบนี้อีก) | เพิ่ม fallback `start=`/`end=` เมื่อ `period="max"` ใช้ไม่ได้ + เติม Open/High/Low ที่เป็น NaN ด้วยค่า Close ก่อนกรองข้อมูล ยังคงเก็บไว้เผื่อ ticker อื่นในอนาคตเจอปัญหาคล้ายกัน แม้ว่า `^SET50` จะไม่ต้องพึ่งอันนี้แล้วหลังเปลี่ยนไปใช้ `TDEX.BK` |
| `Main.py` | แก้ | ตัดระบบ score/hybrid ของ DW ออกทั้งหมด, ส่งทุกสัญญาณที่ผ่าน filter แทนการเลือก top-3 ด้วย score, แยก `run_scan_cycle(force_send)` ออกมาให้ใช้ได้ทั้งแบบ loop ต่อเนื่องและแบบรันครั้งเดียว, แก้ `send_queue()`/`run_scan_cycle()` ที่เดิม report ว่า "ส่งสำเร็จ" เสมอแม้ `send_line()` จะคืนค่า `False` จริง (เช่นไม่มี Token) — ตอนนี้ค่าที่คืนสะท้อนผลจริงแล้ว |
| `dw_scanner.py` | แก้ | (1) แก้ import ที่ชี้ผิดฟังก์ชัน (`get_dw_database` -> `get_scanner_data`) ซึ่งเดิม crash ทันที (2) เพิ่มการกรองตาม `underlying` ที่ขาดไปเดิม (3) ผสาน Yuanta เข้ากับ BLS |
| `yuanta_api.py` | ใหม่ | ไคลเอนต์ดึงข้อมูล DW จาก `dw19club.com` (Yuanta) endpoint ที่หาเจอผ่าน DevTools |
| `test_pipeline_offline.py` | ใหม่ | เทสต์จำลองข้อมูล ไม่ต้องต่อเน็ต ครอบคลุมจุดที่แก้ทั้งหมดข้างต้น |

## Known gap ที่ยังไม่ได้ทำ (ยังไม่ต้องรีบ)

- ยังไม่มีข้อมูลจากค่าย KGI / Maybank Kim Eng / Macquarie (มีแค่ BLS + Yuanta) — ใช้วิธีเดียวกับที่หา
  Yuanta ได้ (DevTools -> Network -> Fetch/XHR) ถ้าต้องการเพิ่มทีหลัง
- โมดูล "หุ้นนำตลาด" (ตรวจเงินไหลเข้า/ออก) ตามที่ระบุในเอกสารตั้งต้น ยังไม่มีในโค้ด
- ยังไม่เคยเทสต์ `yuanta_api.py` กับ endpoint จริงจนจบ (แค่ยืนยัน field mapping ถูกต้องด้วย mock)
  ลองรันจริงบนเครื่องที่ต่อเน็ตได้แล้วดูว่า `dw19club.com` ตอบกลับปกติไหม
