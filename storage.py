import os
import json
import time
import shutil
import threading
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TRADES_FILE = os.path.join(BASE_DIR, "active_trades.json")
BACKUP_FILE = os.path.join(BASE_DIR, "active_trades.bak")
TEMP_FILE = os.path.join(BASE_DIR, "active_trades.tmp")

trade_lock = threading.RLock()

REQUIRED_FIELDS = [
    "symbol",
    "buy_price",
    "amount",
    "buy_time"
]


def _validate_trade(trade):
    if not isinstance(trade, dict):
        return False

    for field in REQUIRED_FIELDS:
        if field not in trade:
            return False

    return True


def load_trades():

    with trade_lock:

        for filename in [TRADES_FILE, BACKUP_FILE]:

            if not os.path.exists(filename):
                continue

            for retry in range(3):

                try:

                    with open(filename, "r") as f:
                        data = json.load(f)

                    if not isinstance(data, list):
                        raise ValueError("Trade file is not list")

                    valid = []

                    for trade in data:
                        if _validate_trade(trade):
                            valid.append(trade)

                    print(f"[STORAGE] Loaded {len(valid)} trades")

                    return valid

                except Exception as e:

                    print(f"[STORAGE] Load retry {retry+1}: {e}")
                    time.sleep(0.5 * (retry + 1))

        print("[STORAGE] No valid trade file found")

        return []


def save_trades(active_trades):

    with trade_lock:

        snapshot = deepcopy(active_trades)

        for retry in range(3):

            try:

                with open(TEMP_FILE, "w") as f:
                    json.dump(snapshot, f, indent=4)

                os.replace(TEMP_FILE, TRADES_FILE)

                shutil.copy2(TRADES_FILE, BACKUP_FILE)

                return True

            except Exception as e:

                print(f"[STORAGE] Save retry {retry+1}: {e}")
                time.sleep(0.5 * (retry + 1))

        print("[STORAGE] Save failed")

        return False


def add_trade(active_trades, trade):

    with trade_lock:

        active_trades.append(trade)

        save_trades(active_trades)


def remove_trade(active_trades, trade):

    with trade_lock:

        if trade in active_trades:
            active_trades.remove(trade)

            save_trades(active_trades)


def update_trade(active_trades):

    with trade_lock:

        save_trades(active_trades)


def backup_exists():
    return os.path.exists(BACKUP_FILE)


def trade_exists(active_trades, symbol):

    with trade_lock:

        for trade in active_trades:
            if trade.get("symbol") == symbol:
                return True

    return False
