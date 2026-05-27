import threading
import time
import config

from scanner import market_data

active_trade = None

def trader_loop():

    global active_trade

    while True:

        try:

            # kalau belum ada posisi
            if active_trade is None:

                for coin in market_data:

                    # hanya entry BUY kuat
                    if coin["signal"] == "STRONG BUY":

                        buy_price = coin["price"]

                        tp_price = buy_price * (
                            1 + config.TAKE_PROFIT / 100
                        )

                        sl_price = buy_price * (
                            1 - config.STOP_LOSS / 100
                        )

                        active_trade = {
                            "symbol": coin["symbol"],
                            "buy_price": buy_price,
                            "current_price": buy_price,
                            "tp_price": tp_price,
                            "sl_price": sl_price,
                            "highest_price": buy_price,
                            "profit_percent": 0,
                            "status": "OPEN"
                        }

                        print(
                            "BUY:",
                            coin["symbol"],
                            buy_price
                        )

                        break

            else:

                # update harga dari scanner
                for coin in market_data:

                    if coin["symbol"] == active_trade["symbol"]:

                        current_price = coin["price"]

                        active_trade["current_price"] = current_price

                        # hitung profit
                        profit = (
                            (
                                current_price -
                                active_trade["buy_price"]
                            )
                            /
                            active_trade["buy_price"]
                        ) * 100

                        active_trade["profit_percent"] = round(
                            profit,
                            2
                        )

                        # update highest
                        if current_price > active_trade["highest_price"]:

                            active_trade["highest_price"] = current_price

                        # trailing stop
                        trailing_price = (
                            active_trade["highest_price"]
                            *
                            (
                                1 -
                                config.TRAILING_GAP / 100
                            )
                        )

                        # TP
                        if current_price >= active_trade["tp_price"]:

                            print(
                                "TAKE PROFIT:",
                                active_trade["symbol"]
                            )

                            active_trade = None

                            break

                        # SL
                        elif current_price <= active_trade["sl_price"]:

                            print(
                                "STOP LOSS:",
                                active_trade["symbol"]
                            )

                            active_trade = None

                            break

                        # TRAILING STOP
                        elif (
                            config.TRAILING_STOP
                            and
                            current_price <= trailing_price
                            and
                            profit > 0
                        ):

                            print(
                                "TRAILING STOP:",
                                active_trade["symbol"]
                            )

                            active_trade = None

                            break

        except Exception as e:

            print("TRADER ERROR:", e)

        time.sleep(10)


def start_trader():

    thread = threading.Thread(
        target=trader_loop
    )

    thread.daemon = True

    thread.start()
