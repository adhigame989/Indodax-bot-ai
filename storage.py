import json
import os

TRADE_FILE = "trade.json"


def save_trade(trade_data):

    try:

        with open(
            TRADE_FILE,
            "w"
        ) as file:

            json.dump(
                trade_data,
                file,
                indent=4
            )

        print("TRADE SAVED")

    except Exception as e:

        print(
            "SAVE TRADE ERROR:",
            str(e)
        )


def load_trade():

    try:

        if not os.path.exists(
            TRADE_FILE
        ):

            return None

        with open(
            TRADE_FILE,
            "r"
        ) as file:

            data = json.load(file)

        print("TRADE LOADED")

        return data

    except Exception as e:

        print(
            "LOAD TRADE ERROR:",
            str(e)
        )

        return None


def clear_trade():

    try:

        if os.path.exists(
            TRADE_FILE
        ):

            os.remove(
                TRADE_FILE
            )

        print("TRADE CLEARED")

    except Exception as e:

        print(
            "CLEAR TRADE ERROR:",
            str(e)
        )
