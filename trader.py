import threading
import time
import ccxt
import config
import scanner

exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trade = None


def trader_loop():

    global active_trade

    print("TRADER STARTED")

    while True:

        try:

            print("TRADER LOOP RUNNING")

            market_data = scanner.market_data

            print("MARKET DATA LENGTH:", len(market_data))

            # BELUM ADA POSISI
            if active_trade is None:

                for coin in market_data:

                    print("CHECK COIN:", coin["symbol"])

                    print("SIGNAL:", coin["signal"])

                    # ENTRY BUY
                    if coin["signal"] not in [
                        "STRONG BUY",
                        "BUY"
                    ]:
                        continue

                    buy_price = coin["price"]

                    amount = round(
                        config.BASE_TRADE_AMOUNT
                        / buy_price,
                        8
                    )

                    print(
                        "TRY BUY:",
                        coin["symbol"]
                    )

                    try:

                        order = exchange.create_market_buy_order(
                            coin["symbol"],
                            amount
                        )

                        print(
                            "BUY SUCCESS:",
                            order
                        )

                        tp_price = buy_price * (
                            1 +
                            config.TAKE_PROFIT / 100
                        )

                        sl_price = buy_price * (
                            1 -
                            config.STOP_LOSS / 100
                        )

                        active_trade = {
                            "symbol": coin["symbol"],
                            "buy_price": buy_price,
                            "current_price": buy_price,
                            "tp_price": tp_price,
                            "sl_price": sl_price,
                            "highest_price": buy_price,
                            "profit_percent": 0,
                            "amount": amount
                        }

                        break

                    except Exception as e:

                        print(
                            "BUY ERROR:",
                            str(e)
                        )

            # ADA POSISI
            else:

                print(
                    "ACTIVE POSITION:",
                    active_trade["symbol"]
                )

                for coin in market_data:

                    if coin["symbol"] != active_trade["symbol"]:
                        continue

                    current_price = coin["price"]

                    active_trade["current_price"] = current_price

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

                    # highest update
                    if current_price > active_trade["highest_price"]:

                        active_trade["highest_price"] = current_price

                    trailing_price = (
                        active_trade["highest_price"]
                        *
                        (
                            1 -
                            config.TRAILING_GAP / 100
                        )
                    )

                    # TAKE PROFIT
                    if current_price >= active_trade["tp_price"]:

                        print("TAKE PROFIT SELL")

                        exchange.create_market_sell_order(
                            active_trade["symbol"],
                            active_trade["amount"]
                        )

                        active_trade = None

                        break

                    # STOP LOSS
                    elif current_price <= active_trade["sl_price"]:

                        print("STOP LOSS SELL")

                        exchange.create_market_sell_order(
                            active_trade["symbol"],
                            active_trade["amount"]
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

                        print("TRAILING STOP SELL")

                        exchange.create_market_sell_order(
                            active_trade["symbol"],
                            active_trade["amount"]
                        )

                        active_trade = None

                        break

        except Exception as e:

            print("TRADER ERROR:", str(e))

        time.sleep(15)


def start_trader():

    print("STARTING TRADER THREAD")

    thread = threading.Thread(
        target=trader_loop
    )

    thread.daemon = True

    thread.start()
