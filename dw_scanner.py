# ==========================================
# DW SCANNER V9.1 PROFESSIONAL
# BLS V11.3 FILTER ENGINE
# DATA FILTER ONLY - NO SCORE
# ==========================================

import logging


from bls_api import get_scanner_data

try:
    from yuanta_api import get_dw_by_underlying as get_yuanta_dw
except Exception:
    # ถ้ายังไม่มีไฟล์ yuanta_api.py หรือ import พัง ให้ระบบยังทำงานต่อได้
    # ด้วย BLS อย่างเดียว (ไม่ crash ทั้งระบบเพราะ Yuanta)
    get_yuanta_dw = None



logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)



# ==========================================
# CONFIG
# ==========================================


MIN_SENSITIVITY = 0.95

MIN_DELTA = 0.30

MIN_GEARING = 5

MIN_DAYS = 30

MAX_SPREAD = 0.02


ALLOW_ISSUER = [

    "BLS",
    "YUANTA",
    "KGI",
    "KS",
    "MST"

]


RETURN_LIMIT = 5





# ==========================================
# SAFE
# ==========================================


def safe_float(value):

    try:

        return float(value)

    except:

        return 0.0





def safe_int(value):

    try:

        return int(value)

    except:

        return 0





# ==========================================
# FILTER CHECK
# ==========================================


def pass_filter(dw, trend):


    dw_type = str(

        dw.get(
            "type",
            ""

        )

    ).upper()



    # ----------------------------
    # CALL / PUT Direction
    # ----------------------------


    if trend == "BUY":

        if dw_type != "CALL":

            return False



    elif trend == "SELL":

        if dw_type != "PUT":

            return False





    # ----------------------------
    # Issuer
    # ----------------------------

    issuer = str(

        dw.get(
            "issuer",
            ""

        )

    ).upper()



    # BLS V11.3 บาง endpoint ไม่มี issuer
    # ถ้ามีค่อยตรวจ

    if issuer:

        if issuer not in ALLOW_ISSUER:

            return False





    # ----------------------------
    # Sensitivity
    # ----------------------------


    sensitivity = safe_float(

        dw.get(
            "sensitivity"
        )

    )


    if sensitivity < MIN_SENSITIVITY:

        return False





    # ----------------------------
    # Delta
    # ----------------------------


    delta = safe_float(

        dw.get(
            "delta",

            dw.get(
                "abs_delta",
                0
            )

        )

    )


    delta = abs(delta)


    if delta < MIN_DELTA:

        return False





    # ----------------------------
    # Gearing
    # ----------------------------


    gearing = safe_float(

        dw.get(
            "effective_gearing"
        )

    )


    if gearing < MIN_GEARING:

        return False





    # ----------------------------
    # Days
    # ----------------------------


    days = safe_int(

        dw.get(
            "days_left"
        )

    )


    if days < MIN_DAYS:

        return False





    # ----------------------------
    # Spread
    # ----------------------------


    spread = safe_float(

        dw.get(
            "spread"
        )

    )


    if spread > MAX_SPREAD:

        return False





    # ----------------------------
    # Liquidity
    # ----------------------------


    liquidity = str(

        dw.get(
            "liquidity",
            ""

        )

    ).upper()



    if liquidity == "WIDE":

        return False





    return True







# ==========================================
# SORT QUALITY
# ==========================================


def sort_quality(dw):

    """
    เรียงคุณภาพ DW
    ไม่ใช่ Score
    """


    return (

        safe_float(

            dw.get(
                "sensitivity"
            )

        ),


        abs(

            safe_float(

                dw.get(
                    "delta"
                )

            )

        ),


        safe_float(

            dw.get(
                "effective_gearing"
            )

        ),


        safe_int(

            dw.get(
                "days_left"
            )

        )

    )








# ==========================================
# MAIN SCANNER
# ==========================================


def get_filtered_dw(

        underlying="SET50",

        trend="BUY"

):


    logging.info(

        f"DW FILTER START | {underlying} | {trend}"

    )



    raw = list(get_scanner_data() or [])

    # เพิ่ม Yuanta (dw19club.com) เข้ามารวมกับ BLS
    # ขอเฉพาะ underlying ที่ต้องการตรง ๆ (API ของ Yuanta filter ได้เอง)
    if get_yuanta_dw is not None:

        try:
            yuanta_raw = get_yuanta_dw(underlying)

            if yuanta_raw:
                raw += yuanta_raw

        except Exception as e:
            logging.warning(f"YUANTA MERGE FAIL : {e}")

    if not raw:


        logging.warning(

            "NO DW DATA (BLS + YUANTA)"

        )


        return []





    result = []



    target_underlying = str(underlying).upper()

    for dw in raw:

        dw_underlying = str(
            dw.get("underlying", "")
        ).upper()

        # ต้องเป็น DW ของหุ้น/ดัชนีตัวที่ขอจริง ๆ
        # (get_scanner_data คืนมาทุกตัวรวมกัน ไม่ได้กรองมาก่อน)
        if dw_underlying != target_underlying:
            continue

        if pass_filter(

            dw,

            trend

        ):

            result.append(dw)







    result.sort(

        key=sort_quality,

        reverse=True

    )





    logging.info(

        f"DW FILTER RESULT : {len(result)}"

    )





    return result[:RETURN_LIMIT]









# ==========================================
# COMPATIBILITY
# ==========================================


def get_best_dw(

        underlying,

        trend="BUY"

):

    """
    Backward compatible
    Main.py เดิมใช้ได้
    """


    return get_filtered_dw(

        underlying,

        trend

    )









# ==========================================
# TEST
# ==========================================


if __name__ == "__main__":



    result = get_filtered_dw(

        "SET50",

        "BUY"

    )



    print()

    print("="*60)

    print(

        "FILTERED DW RESULT"

    )

    print("="*60)





    for dw in result:


        print(

            f"{dw.get('symbol',''):15}"

            f"{dw.get('type',''):5}"

            f"Sens={dw.get('sensitivity',0):.2f} "

            f"Gear={dw.get('effective_gearing',0):.2f} "

            f"Delta={dw.get('delta',0):.2f} "

            f"Days={dw.get('days_left',0)} "

            f"Spread={dw.get('spread',0):.3f}"

        )