import time
import logging

from config import (
    PRICE_CACHE_TTL,
    DW_CACHE_TTL,
    MAX_ALERT_MEMORY,
)


# ==========================================
# CACHE GET
# ==========================================

def get_cache(cache, key, ttl):

    try:

        if key not in cache:
            return None


        cache_time, data = cache[key]


        if time.monotonic() - cache_time > ttl:

            del cache[key]

            logging.info(
                f"CACHE EXPIRED : {key}"
            )

            return None


        return data


    except Exception as e:

        logging.error(
            f"GET CACHE ERROR {key}: {e}"
        )

        return None



# ==========================================
# CACHE SAVE
# ==========================================

def save_cache(cache, key, data):

    try:

        cache[key] = (
            time.monotonic(),
            data
        )


    except Exception as e:

        logging.error(
            f"SAVE CACHE ERROR {key}: {e}"
        )



# ==========================================
# CLEANUP ALL CACHE
# ==========================================

def cleanup_cache(price_cache, dw_cache, last_alerts):

    now = time.monotonic()


    # ======================================
    # PRICE CACHE
    # ======================================

    remove_price = []


    for key, value in list(price_cache.items()):

        try:

            cache_time = value[0]

            if now - cache_time > PRICE_CACHE_TTL:
                remove_price.append(key)


        except:

            remove_price.append(key)



    for key in remove_price:

        del price_cache[key]

        logging.info(
            f"PRICE CACHE REMOVED : {key}"
        )



    # ======================================
    # DW CACHE
    # ======================================

    remove_dw = []


    for key, value in list(dw_cache.items()):

        try:

            if not isinstance(value, tuple):
                remove_dw.append(key)
                continue


            cache_time = value[0]


            if now - cache_time > DW_CACHE_TTL:
                remove_dw.append(key)



        except:

            remove_dw.append(key)



    for key in remove_dw:

        del dw_cache[key]

        logging.info(
            f"DW CACHE EXPIRED : {key}"
        )



    # ======================================
    # ALERT MEMORY
    # ======================================

    if len(last_alerts) > MAX_ALERT_MEMORY:


        old_items = sorted(
            last_alerts.items(),
            key=lambda x:x[1][0]
        )


        remove_count = (
            len(last_alerts)
            -
            MAX_ALERT_MEMORY
        )


        for i in range(remove_count):

            key = old_items[i][0]

            del last_alerts[key]


            logging.info(
                f"ALERT REMOVED : {key}"
            )