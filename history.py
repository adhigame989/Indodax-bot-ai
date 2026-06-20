import json
import os
from datetime import datetime, timedelta

HISTORY_FILE = "/data/history.json"
os.makedirs("/data", exist_ok=True)


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
    profit_percent,
    profit_idr,
    entry_value,
    reason=None,
    buy_reason=None,
    buy_score=None

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

            "profit_idr": round(profit_idr, 0),
            "entry_value": round(entry_value, 0),
            "reason": reason,
            "buy_reason": buy_reason,
            "buy_score": buy_score,

            "time":
            (
                datetime.utcnow()
                + timedelta(hours=7)
            ).strftime(
                "%Y-%m-%d %H:%M:%S WIB"
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
    total_profit_idr = 0
    total_modal = 0
    tp_count = 0
    sl_count = 0
    trailing_count = 0
    manual_count = 0

    buy_count = 0
    strong_buy_count = 0

    buy_win = 0
    strong_buy_win = 0

    win_scores = []
    loss_scores = []

    for trade in history:

        profit_idr = trade.get("profit_idr", 0)
        entry_value = trade.get("entry_value", 0)

        total_profit_idr += profit_idr
        total_modal += entry_value
        reason = trade.get("reason", "")
        buy_reason = trade.get("buy_reason", "")
        buy_score = trade.get("buy_score", 0)

        if reason == "TP":
            tp_count += 1
        elif reason == "SL":
            sl_count += 1
        elif reason == "TRAILING":
            trailing_count += 1
        elif reason == "MANUAL":
            manual_count += 1

        if buy_reason == "BUY":
            buy_count += 1
            if profit_idr > 0:
                buy_win += 1

        elif buy_reason == "STRONG BUY":
            strong_buy_count += 1
            if profit_idr > 0:
                strong_buy_win += 1

        try:
            buy_score = float(buy_score)
            if profit_idr > 0:
                win_scores.append(buy_score)
            else:
                loss_scores.append(buy_score)
        except:
            pass
        
        if profit_idr > 0:
            win += 1
        else:
            loss += 1

    winrate = 0

    if total_trades > 0:

        winrate = (
            win / total_trades
        ) * 100

    real_profit_percent = 0

    if total_modal > 0:
        real_profit_percent = (
            total_profit_idr / total_modal
    ) * 100

    buy_winrate = round((buy_win / buy_count * 100), 2) if buy_count > 0 else 0
    strong_buy_winrate = round((strong_buy_win / strong_buy_count * 100), 2) if strong_buy_count > 0 else 0

    avg_win_score = round(sum(win_scores) / len(win_scores), 2) if win_scores else 0
    avg_loss_score = round(sum(loss_scores) / len(loss_scores), 2) if loss_scores else 0
    return {

        "total_trades":total_trades,

        "win":win,

        "loss":loss,

        "winrate":round(winrate, 2),

        "total_profit":round(real_profit_percent, 2),

        "total_profit_idr": round(total_profit_idr, 0),

        "history":history,

        "tp_count": tp_count,
        "sl_count": sl_count,
        "trailing_count": trailing_count,
        "manual_count": manual_count,

        "buy_winrate": buy_winrate,
        "strong_buy_winrate": strong_buy_winrate,

        "avg_win_score": avg_win_score,
        "avg_loss_score": avg_loss_score,

    }
