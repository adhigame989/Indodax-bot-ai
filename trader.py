import threading
import time
import ccxt
import config
import scanner

from storage import (
    save_trade,
    load_trade,
    clear_trade
)

exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trade = load_trade()


def sync_wallet():

    try:

        balance = exchange.fetch_balance()

        print("WALLET SYNC SUCCESS")

        return balance

    except Exception as e:

        print("SYNC ERROR:", str(e))

        return None


def cancel_all_orders():

    try:

        orders = exchange.fetch_open_orders()

        print("OPEN ORDERS:", len(orders))

        for order in orders:

            try:

                exchange.cancel_order(
                    order['id'],
                    order['symbol'],
                    {
                        'side': order['side']
                    }
                )

                print(
                    "ORDER CANCELLED:",
                    order['id']
                )

            except Exception as e:

                print(
                    "CANCEL ERROR:",
                    str(e)
                )

    except Exception as e:

        print(
            "FETCH ORDER ERROR:",
            str(e)
        )


def get_idr_balance():

    try:

        balance = exchange.fetch_balance()

        idr = balance['total'].get(
            'IDR',
            0
        )

        return float(idr)

    except Exception as e:

        print(
            "BALANCE ERROR:",
            str(e)
        )

        return 0


def buy_coin(symbol, buy_price):

    try:

        idr_balance = get_idr_balance()

        print(
            "IDR BALANCE:",
            idr_balance
        )

        if (
            idr_balance <
            config.BASE_TRADE_AMOUNT
        ):

            print("NOT ENOUGH IDR")

            return None

        amount = (
            config.BASE_TRADE_AMOUNT
            / buy_price
        )

        amount = round(amount, 8)

        buy_price = buy_price * (
            1 +
            config.BUY_SLIPPAGE
        )

        buy_price = round(
            buy_price,
            8
        )

        print(
            "BUY ORDER:",
            symbol,
            amount,
            buy_price
        )

        order = exchange.create_order(
            symbol=symbol,
            type="limit",
            side="buy",
            amount=amount,
            price=buy_price
        )

        print("BUY SUCCESS:", order)

        return {

            "amount":
            amount,

            "order":
            order,

            "buy_price":
            buy_price

        }

    except Exception as e:

        print(
            "BUY ERROR:",
            str(e)
        )

        return None


def sell_coin(
    symbol,
    amount,
    sell_price
):

    try:

        amount = round(amount, 8)

        sell_price = sell_price * (
            1 -
            config.SELL_SLIPPAGE
        )

        sell_price = round(
            sell_price,
            8
        )

        print(
            "SELL ORDER:",
            symbol,
            amount,
            sell_price
        )

        order = exchange.create_order(
            symbol=symbol,
            type="limit",
            side="sell",
            amount=amount,
            price=sell_price
        )

        print(
            "SELL SUCCESS:",
            order
        )

        return order

    except Exception as e:

        print(
            "SELL ERROR:",
            str(e)
        )

        return None


def trader_loop():

    global active_trade

    print("TRADER STARTED")

    cancel_all_orders()

    sync_wallet()

    while True:

        try:

            market_data = (
                scanner.market_data
            )

            print(
                "MARKET DATA LENGTH:",
                len(market_data)
            )

            if active_trade is None:

                print(
                    "SEARCHING ENTRY..."
                )

                for coin in market_data:

                    print(
                        "CHECK:",
                        coin["symbol"],
                        coin["signal"],
                        coin["score"]
                    )

                    if coin["signal"] not in [
                        "STRONG BUY",
                        "BUY"
                    ]:
                        continue

                    buy_price = float(
                        coin["price"]
                    )

                    print(
                        "TRY BUY:",
                        coin["symbol"]
                    )

                    buy_result = buy_coin(
                        coin["symbol"],
                        buy_price
                    )

                    if buy_result:

                        amount = (
                            buy_result["amount"]
                        )

                        real_buy_price = (
                            buy_result["buy_price"]
                        )

                        tp_price = (
                            real_buy_price
                            *
                            (
                                1 +
                                config.TAKE_PROFIT
                                / 100
                            )
                        )

                        sl_price = (
                            real_buy_price
                            *
                            (
                                1 -
                                config.STOP_LOSS
                                / 100
                            )
                        )

                        active_trade = {

                            "symbol":
                            coin["symbol"],

                            "buy_price":
                            real_buy_price,

                            "current_price":
                            real_buy_price,

                            "tp_price":
                            tp_price,

                            "sl_price":
                            sl_price,

                            "highest_price":
                            real_buy_price,

                            "profit_percent":
                            0,

                            "amount":
                            amount,

                            "status":
                            "OPEN"

                        }

                        save_trade(
                            active_trade
                        )

                        print(
                            "ACTIVE TRADE:",
                            active_trade
                        )

                        break

            else:

                print(
                    "MONITORING:",
                    active_trade["symbol"]
                )

                for coin in market_data:

                    if (
                        coin["symbol"]
                        !=
                        active_trade["symbol"]
                    ):
                        continue

                    current_price = float(
                        coin["price"]
                    )

                    active_trade[
                        "current_price"
                    ] = current_price

                    profit = (
                        (
                            current_price
                            -
                            active_trade[
                                "buy_price"
                            ]
                        )
                        /
                        active_trade[
                            "buy_price"
                        ]
                    ) * 100

                    active_trade[
                        "profit_percent"
                    ] = round(
                        profit,
                        2
                    )

                    print(
                        "CURRENT PROFIT:",
                        active_trade[
                            "profit_percent"
                        ]
                    )

                    if (
                        current_price >
                        active_trade[
                            "highest_price"
                        ]
                    ):

                        active_trade[
                            "highest_price"
                        ] = current_price

                        save_trade(
                            active_trade
                        )

                    trailing_price = (
                        active_trade[
                            "highest_price"
                        ]
                        *
                        (
                            1 -
                            config.TRAILING_GAP
                            / 100
                        )
                    )

                    if (
                        current_price >=
                        active_trade[
                            "tp_price"
                        ]
                    ):

                        print(
                            "TAKE PROFIT HIT"
                        )

                        sell_result = sell_coin(
                            active_trade[
                                "symbol"
                            ],
                            active_trade[
                                "amount"
                            ],
                            current_price
                        )

                        if sell_result:

                            print(
                                "TP SELL SUCCESS"
                            )

                            clear_trade()

                            active_trade = None

                        break

                    elif (
                        current_price <=
                        active_trade[
                            "sl_price"
                        ]
                    ):

                        print(
                            "STOP LOSS HIT"
                        )

                        sell_result = sell_coin(
                            active_trade[
                                "symbol"
                            ],
                            active_trade[
                                "amount"
                            ],
                            current_price
                        )

                        if sell_result:

                            print(
                                "SL SELL SUCCESS"
                            )

                            clear_trade()

                            active_trade = None

                        break

                    elif (

                        config.TRAILING_STOP

                        and

                        current_price <=
                        trailing_price

                        and

                        profit > 0

                    ):

                        print(
                            "TRAILING STOP HIT"
                        )

                        sell_result = sell_coin(
                            active_trade[
                                "symbol"
                            ],
                            active_trade[
                                "amount"
                            ],
                            current_price
                        )

                        if sell_result:

                            print(
                                "TRAILING SELL SUCCESS"
                            )

                            clear_trade()

                            active_trade = None

                        break

        except Exception as e:

            print(
                "TRADER ERROR:",
                str(e)
            )

        time.sleep(
            config.TRADER_INTERVAL
        )


def start_trader():

    print(
        "STARTING TRADER THREAD"
    )

    thread = threading.Thread(
        target=trader_loop
    )

    thread.daemon = True

    thread.start()
