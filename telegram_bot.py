import requests
import os

BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    ""
)

CHAT_ID = os.environ.get(
    "TELEGRAM_CHAT_ID",
    ""
)


def send_telegram(message):

    try:

        if not BOT_TOKEN:
            return

        if not CHAT_ID:
            return

        url = (
            f"https://api.telegram.org/bot"
            f"{BOT_TOKEN}/sendMessage"
        )

        data = {

            "chat_id":
            CHAT_ID,

            "text":
            message

        }

        requests.post(
            url,
            data=data,
            timeout=10
        )

        print(
            "TELEGRAM SENT"
        )

    except Exception as e:

        print(
            "TELEGRAM ERROR:",
            str(e)
        )
