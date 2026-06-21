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

    hold_times=[]
    fastest_tp=None
    longest_hold=0
    profit_list=[]

    buy_tp=0
    buy_sl=0
    buy_trail=0

    strong_tp=0
    strong_sl=0
    strong_trail=0

    score_buckets = {
        "80_89": {"win": 0, "loss": 0},
        "90_99": {"win": 0, "loss": 0},
        "100_109": {"win": 0, "loss": 0},
        "110_119": {"win": 0, "loss": 0},
        "120_plus": {"win": 0, "loss": 0},
    }

    for trade in history:

        profit_idr = trade.get("profit_idr", 0)
        entry_value = trade.get("entry_value", 0)

        total_profit_idr += profit_idr
        total_modal += entry_value
        reason = trade.get("reason", "")
        buy_reason = trade.get("buy_reason", "")
        buy_score = trade.get("buy_score", 0)
        profit_list.append(trade.get("profit_percent",0))
        hold_sec=trade.get("hold_duration",0)

        if hold_sec>0:
            hold_times.append(hold_sec)

            if hold_sec>longest_hold:
                longest_hold=hold_sec

            if reason in ["TP", "TAKE_PROFIT"]:
                if fastest_tp is None or hold_sec<fastest_tp:
                    fastest_tp=hold_sec

        if reason in ["TP", "TAKE_PROFIT"]:
            tp_count += 1

        elif reason in ["SL", "STOP_LOSS"]:
            sl_count += 1

        elif reason in ["TRAIL", "TRAILING", "TRAILING_STOP"]:
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
        if buy_reason=="BUY":
            if reason=="TP":
                buy_tp+=1
            elif reason=="SL":
                buy_sl+=1
            elif reason=="TRAILING":
                buy_trail+=1

        elif buy_reason=="STRONG BUY":
            if reason=="TP":
                strong_tp+=1
            elif reason=="SL":
                strong_sl+=1
            elif reason=="TRAILING":
                strong_trail+=1

        try:
            buy_score = float(buy_score)
            if profit_idr > 0:
                win_scores.append(buy_score)
            else:
                loss_scores.append(buy_score)

            bs = float(buy_score)

            bucket = None

            if 80 <= bs <= 89:
                bucket = "80_89"
            elif 90 <= bs <= 99:
                bucket = "90_99"
            elif 100 <= bs <= 109:
                bucket = "100_109"
            elif 110 <= bs <= 119:
                bucket = "110_119"
            elif bs >= 120:
                bucket = "120_plus"

            if bucket:
                if profit_idr > 0:
                    score_buckets[bucket]["win"] += 1
                else:
                    score_buckets[bucket]["loss"] += 1

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

    avg_hold=sum(hold_times)/len(hold_times) if hold_times else 0
    avg_profit=round(sum(profit_list)/len(profit_list),2) if profit_list else 0
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
        "buy_tp":buy_tp,
        "buy_sl":buy_sl,
        "buy_trail":buy_trail,

        "strong_tp":strong_tp,
        "strong_sl":strong_sl,
        "strong_trail":strong_trail,

        "score_buckets": score_buckets,

        "avg_hold": avg_hold,
        "fastest_tp": fastest_tp or 0,
        "longest_hold": longest_hold,
        "avg_profit": avg_profit,

    }
