import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"


def load_history():

    try:

        if not os.path.exists(
            HISTORY_FILE
        ):

            return []

        with open(
            HISTORY_FILE,
            "r"
        ) as file:

            data = json.load(file)

        return data

    except Exception as e:

        print(
            "LOAD HISTORY ERROR:",
            str(e)
        )

        return []


def save_history(history):

    try:

        with open(
            HISTORY_FILE,
            "w"
        ) as file:

            json.dump(
                history,
                file,
                indent=4
            )

    except Exception as e:

        print(
            "SAVE HISTORY ERROR:",
            str(e)
        )


def add_trade_history(

    symbol,
    side,
    buy_price,
    sell_price,
    profit_percent

):

    try:

        history = load_history()

        trade = {

            "symbol":
            symbol,

            "side":
            side,

            "buy_price":
            buy_price,

            "sell_price":
            sell_price,

            "profit_percent":
            round(
                profit_percent,
                2
            ),

            "time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        }

        history.insert(
            0,
            trade
        )

        # batasi 100 trade
        history = history[:100]

        save_history(history)

        print(
            "TRADE HISTORY SAVED"
        )

    except Exception as e:

        print(
            "ADD HISTORY ERROR:",
            str(e)
        )


def get_stats():

    history = load_history()

    total_trades = len(history)

    win = 0
    loss = 0

    total_profit = 0

    for trade in history:

        profit = trade.get(
            "profit_percent",
            0
        )

        total_profit += profit

        if profit > 0:
            win += 1
        else:
            loss += 1

    winrate = 0

    if total_trades > 0:

        winrate = (
            win / total_trades
        ) * 100

    return {

        "total_trades":
        total_trades,

        "win":
        win,

        "loss":
        loss,

        "winrate":
        round(winrate, 2),

        "total_profit":
        round(total_profit, 2),

        "history":
        history

    }
