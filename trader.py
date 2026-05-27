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

from telegram_bot import (
    send_telegram
)

from history import (
    add_trade_history
)

exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trade = load_trade()

cooldown_until = 0

loss_streak = 0


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


def get_trade_amount():

    try:

        balance = exchange.fetch_balance()

        idr = float(
            balance['total'].get(
                'IDR',
                0
            )
        )

        compound_amount = (
            idr *
            config.COMPOUND_PERCENT
        ) / 100

        if (
            compound_amount <
            config.BASE_TRADE_AMOUNT
        ):

            compound_amount = (
                config.BASE_TRADE_AMOUNT
            )

        if (
            compound_amount >
            config.MAX_TRADE_AMOUNT
        ):

            compound_amount = (
                config.MAX_TRADE_AMOUNT
            )

        print(
            "COMPOUND TRADE AMOUNT:",
            compound_amount
        )

        return compound_amount

    except Exception as e:

        print(
            "COMPOUND ERROR:",
            str(e)
        )

        return config.BASE_TRADE_AMOUNT


def get_best_prices(symbol):

    try:

        orderbook = exchange.fetch_order_book(
            symbol
        )

        best_ask = None
        best_bid = None

        if orderbook['asks']:

            best_ask = orderbook[
                'asks'
            ][0][0]

        if orderbook['bids']:

            best_bid = orderbook[
                'bids'
            ][0][0]

        return best_ask, best_bid

    except Exception as e:

        print(
            "ORDERBOOK ERROR:",
            str(e)
        )

        return None, None


def wait_order_filled(
    order_id,
    symbol
):

    try:

        print(
            "WAITING ORDER FILLED:",
            order_id
        )

        for i in range(20):

            try:

                orders = exchange.fetch_open_orders(
                    symbol
                )

                still_open = False

                for order in orders:

                    if (
                        str(order['id'])
                        ==
                        str(order_id)
                    ):

                        still_open = True
                        break

                if not still_open:

                    print(
                        "ORDER FILLED:",
                        order_id
                    )

                    return True

                print(
                    "ORDER STILL OPEN:",
                    order_id
                )

            except Exception as e:

                print(
                    "CHECK ORDER ERROR:",
                    str(e)
                )

            time.sleep(3)

        try:

            exchange.cancel_order(
                order_id,
                symbol,
                {
                    'side': 'buy'
                }
            )

            print(
                "ORDER TIMEOUT CANCELLED:",
                order_id
            )

        except Exception as e:

            print(
                "CANCEL TIMEOUT ERROR:",
                str(e)
            )

        return False

    except Exception as e:

        print(
            "WAIT FILLED ERROR:",
            str(e)
        )

        return False


def buy_coin(symbol):

    try:

        idr_balance = get_idr_balance()

        print(
            "IDR BALANCE:",
            idr_balance
        )

        trade_amount = get_trade_amount()

        if idr_balance < trade_amount:

            print("NOT ENOUGH IDR")

            return None

        best_ask, best_bid = get_best_prices(
            symbol
        )

        if not best_ask:

            print("NO BEST ASK")

            return None

        buy_price = best_ask * (
            1 +
            config.BUY_SLIPPAGE
        )

        buy_price = round(
            buy_price,
            8
        )

        amount = (
            trade_amount
            / buy_price
        )

        amount = round(
            amount,
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

        print(
            "BUY SUCCESS:",
            order
        )

        return {

            "amount":
            amount,

            "order":
            order,

            "buy_price":
            buy_price,

            "trade_amount":
            trade_amount

        }

    except Exception as e:

        print(
            "BUY ERROR:",
            str(e)
        )

        send_telegram(
            f"❌ BUY ERROR\n\n{str(e)}"
        )

        return None


def sell_coin(
    symbol,
    amount
):

    try:

        best_ask, best_bid = get_best_prices(
            symbol
        )

        if not best_bid:

            print("NO BEST BID")

            return None

        sell_price = best_bid * (
            1 -
            config.SELL_SLIPPAGE
        )

        sell_price = round(
            sell_price,
            8
        )

        amount = round(
            amount,
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

        send_telegram(
            f"❌ SELL ERROR\n\n{str(e)}"
        )

        return None


def trader_loop():

    global active_trade
    global cooldown_until
    global loss_streak

    print("TRADER STARTED")

    send_telegram(
        "🤖 INDODAX BOT STARTED"
    )

    cancel_all_orders()

    sync_wallet()

    while True:

        try:

            now = time.time()

            market_data = (
                scanner.market_data
            )

            print(
                "MARKET DATA LENGTH:",
                len(market_data)
            )

            if now < cooldown_until:

                remain = int(
                    cooldown_until - now
                )

                print(
                    "COOLDOWN ACTIVE:",
                    remain,
                    "seconds"
                )

                time.sleep(
                    config.TRADER_INTERVAL
                )

                continue

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

                    print(
                        "TRY BUY:",
                        coin["symbol"]
                    )

                    buy_result = buy_coin(
                        coin["symbol"]
                    )

                    if buy_result:

                        order_id = (
                            buy_result["order"]["id"]
                        )

                        filled = wait_order_filled(
                            order_id,
                            coin["symbol"]
                        )

                        if not filled:

                            print(
                                "ORDER NOT FILLED"
                            )

                            continue

                        amount = (
                            buy_result["amount"]
                        )

                        real_buy_price = (
                            buy_result["buy_price"]
                        )

                        trade_amount = (
                            buy_result["trade_amount"]
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

                            "trade_amount":
                            trade_amount,

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

                        send_telegram(
                            f"🟢 BUY\n\n"
                            f"{coin['symbol']}\n"
                            f"Buy: {real_buy_price}\n"
                            f"Modal: Rp {trade_amount:,.0f}"
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

                        sell_result = sell_coin(
                            active_trade[
                                "symbol"
                            ],
                            active_trade[
                                "amount"
                            ]
                        )

                        if sell_result:

                            loss_streak = 0

                            add_trade_history(

                                active_trade["symbol"],
                                "TP",

                                active_trade["buy_price"],

                                current_price,

                                active_trade["profit_percent"]

                            )

                            send_telegram(
                                f"🎯 TAKE PROFIT\n\n"
                                f"{active_trade['symbol']}\n"
                                f"Profit: "
                                f"{active_trade['profit_percent']}%\n"
                                f"Modal: Rp "
                                f"{active_trade['trade_amount']:,.0f}"
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

                        sell_result = sell_coin(
                            active_trade[
                                "symbol"
                            ],
                            active_trade[
                                "amount"
                            ]
                        )

                        if sell_result:

                            loss_streak += 1

                            if loss_streak >= 2:

                                cooldown_until = (
                                    time.time()
                                    + 3600
                                )

                                send_telegram(
                                    "🧊 BOT COOLDOWN 1 HOUR"
                                )

                            else:

                                cooldown_until = (
                                    time.time()
                                    + 1800
                                )

                                send_telegram(
                                    "🧊 BOT COOLDOWN 30 MIN"
                                )

                            add_trade_history(

                                active_trade["symbol"],
                                "SL",

                                active_trade["buy_price"],

                                current_price,

                                active_trade["profit_percent"]

                            )

                            send_telegram(
                                f"🔴 STOP LOSS\n\n"
                                f"{active_trade['symbol']}\n"
                                f"Loss: "
                                f"{active_trade['profit_percent']}%\n"
                                f"Modal: Rp "
                                f"{active_trade['trade_amount']:,.0f}"
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

                        sell_result = sell_coin(
                            active_trade[
                                "symbol"
                            ],
                            active_trade[
                                "amount"
                            ]
                        )

                        if sell_result:

                            loss_streak = 0

                            add_trade_history(

                                active_trade["symbol"],
                                "TRAILING",

                                active_trade["buy_price"],

                                current_price,

                                active_trade["profit_percent"]

                            )

                            send_telegram(
                                f"🚀 TRAILING STOP\n\n"
                                f"{active_trade['symbol']}\n"
                                f"Profit: "
                                f"{active_trade['profit_percent']}%\n"
                                f"Modal: Rp "
                                f"{active_trade['trade_amount']:,.0f}"
                            )

                            clear_trade()

                            active_trade = None

                        break

        except Exception as e:

            print(
                "TRADER ERROR:",
                str(e)
            )

            send_telegram(
                f"❌ TRADER ERROR\n\n{str(e)}"
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
