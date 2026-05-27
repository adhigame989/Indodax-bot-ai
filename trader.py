import threading
import time
import ccxt
import config

from scanner import market_data

exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trade = None


def buy_coin(symbol, price):

    try:

        # hitung jumlah coin
        amount = (
            config.BASE_TRADE_AMOUNT
            / price
        )

        # market buy
        order = exchange.create_market_buy_order(
            symbol,
            amount
        )

        print("BUY SUCCESS:", symbol)

        return order

    except Exception as e:

        print("BUY ERROR:", e)

        return None


def sell_coin(symbol, amount):

    try:

        order = exchange.create_market_sell_order(
            symbol,
            amount
        )

        print("SELL SUCCESS:", symbol)

        return order

    except Exception as e:

        print("SELL ERROR:", e)

        return None


def trader_loop():

    global active_trade

    while True:

        try:

            # ENTRY
            if active_trade is None:

                for coin in market_data:

                    if coin["signal"] != "STRONG BUY":
                        continue

                    buy_price = coin["price"]

                    # REAL BUY
                    order = buy_coin(
                        coin["symbol"],
                        buy_price
                    )

                    if order:

                        amount = (
                            config.BASE_TRADE_AMOUNT
                            / buy_price
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
                            "amount": amount,
                            "status": "OPEN"
                        }

                        print(
                            "ACTIVE TRADE:",
                            active_trade
                        )

                        break

            # MONITOR POSITION
            else:

                for coin in market_data:

                    if coin["symbol"] != active_trade["symbol"]:
                        continue

                    current_price = coin["price"]

                    active_trade["current_price"] = current_price

                    # profit %
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

                    # highest
                    if current_price > active_trade["highest_price"]:

                        active_trade["highest_price"] = current_price

                    # trailing price
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

                        sell_coin(
                            active_trade["symbol"],
                            active_trade["amount"]
                        )

                        print("TAKE PROFIT")

                        active_trade = None

                        break

                    # STOP LOSS
                    elif current_price <= active_trade["sl_price"]:

                        sell_coin(
                            active_trade["symbol"],
                            active_trade["amount"]
                        )

                        print("STOP LOSS")

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

                        sell_coin(
                            active_trade["symbol"],
                            active_trade["amount"]
                        )

                        print("TRAILING STOP")

                        active_trade = None

                        break

        except Exception as e:

            print("TRADER ERROR:", e)

        time.sleep(15)


def start_trader():

    thread = threading.Thread(
        target=trader_loop
    )

    thread.daemon = True

    thread.start()
