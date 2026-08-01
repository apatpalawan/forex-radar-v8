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
# SEND LINE
# ==========================================

def send_line(message):

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



    headers = {

        "Authorization":
            f"Bearer {CHANNEL_ACCESS_TOKEN}",

        "Content-Type":
            "application/json"

    }



    payload = {

        "to":
            LINE_USER_ID,

        "messages": [

            {
                "type":
                    "text",

                "text":
                    str(message)[:5000]
            }

        ]

    }



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
                    "LINE SEND SUCCESS"
                )


                return True



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



    logging.error(
        "LINE SEND FAILED"
    )


    return False