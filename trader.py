import ccxt
import time
import threading
import json
import os
import config
import history
import scanner
import telegram_bot

BOT_RUNNING = False

exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trade = None

trade_file = "active_trade.json"


def save_trade():

    global active_trade

    try:

        with open(
            trade_file,
            "w"
        ) as f:

            json.dump(
                active_trade,
                f
            )

    except Exception as e:

        print(
            "SAVE TRADE ERROR:",
            str(e)
        )


def load_trade():

    global active_trade

    try:

        if os.path.exists(
            trade_file
        ):

            with open(
                trade_file,
                "r"
            ) as f:

                active_trade = json.load(f)

                print(
                    "TRADE LOADED"
                )

    except Exception as e:

        print(
            "LOAD TRADE ERROR:",
            str(e)
        )


def clear_trade():

    global active_trade

    active_trade = None

    try:

        if os.path.exists(
            trade_file
        ):

            os.remove(
                trade_file
            )

    except Exception as e:

        print(
            "CLEAR TRADE ERROR:",
            str(e)
        )


def get_trade_amount(balance):

    try:

        compound_size = (
            balance *
            (
                config.COMPOUND_PERCENT
                / 100
            )
        )

        amount = max(
            config.BASE_TRADE_AMOUNT,
            compound_size
        )

        amount = min(
            amount,
            config.MAX_TRADE_AMOUNT
        )

        return amount

    except Exception as e:

        print(
            "TRADE AMOUNT ERROR:",
            str(e)
        )

        return config.BASE_TRADE_AMOUNT


def buy_coin(symbol):

    global active_trade

    try:

        balance = exchange.fetch_balance()

        idr = balance['free'].get(
            'IDR',
            0
        )

        trade_amount = get_trade_amount(
            idr
        )

        if idr < trade_amount:

            print(
                "NOT ENOUGH IDR"
            )

            return

        ticker = exchange.fetch_ticker(
            symbol
        )

        ask_price = ticker['ask']

        buy_price = (
            ask_price *
            (
                1 +
                config.BUY_SLIPPAGE
            )
        )

        amount = (
            trade_amount /
            buy_price
        )

        order = exchange.create_limit_buy_order(
            symbol,
            amount,
            buy_price
        )

        print(
            "BUY ORDER:",
            symbol
        )

        time.sleep(10)

        try:

            order_info = exchange.fetch_order(
                order['id'],
                symbol
            )

            if (
                order_info['status']
                != 'closed'
            ):

                exchange.cancel_order(
                    order['id'],
                    symbol,
                    {
                        'side': 'buy'
                    }
                )

                print(
                    "BUY CANCELLED:",
                    symbol
                )

                return

        except Exception as e:

            print(
                "BUY CHECK ERROR:",
                str(e)
            )

            return

        tp_price = (
            buy_price *
            (
                1 +
                (
                    config.TAKE_PROFIT
                    / 100
                )
            )
        )

        sl_price = (
            buy_price *
            (
                1 -
                (
                    config.STOP_LOSS
                    / 100
                )
            )
        )

        active_trade = {

            "symbol":
            symbol,

            "buy_price":
            round(
                buy_price,
                8
            ),

            "current_price":
            round(
                buy_price,
                8
            ),

            "tp_price":
            round(
                tp_price,
                8
            ),

            "sl_price":
            round(
                sl_price,
                8
            ),

            "amount":
            amount,

            "highest_price":
            round(
                buy_price,
                8
            ),

            "profit_percent":
            0

        }

        save_trade()

        print(
            "BUY SUCCESS:",
            symbol
        )
        telegram_bot.send_telegram(

            f"🟢 BUY SUCCESS\n\n"
            f"Coin: {symbol}\n"
            f"Buy Price: {buy_price:.8f}\n"
            f"TP: {tp_price:.8f}\n"
            f"SL: {sl_price:.8f}"

        )

    except Exception as e:

        print(
            "BUY ERROR:",
            str(e)
        )


def sell_coin():

    global active_trade

    try:

        if not active_trade:
            return

        symbol = active_trade[
            "symbol"
        ]

        base_coin = symbol.split("/")[0]

        balance = exchange.fetch_balance()

        amount = balance["free"].get(
            base_coin,
            0
        )
        ticker = exchange.fetch_ticker(
            symbol
        )

        bid_price = ticker['bid']

        sell_price = (
            bid_price *
            (
                1 -
                config.SELL_SLIPPAGE
            )
        )

        order = exchange.create_limit_sell_order(
            symbol,
            amount,
            sell_price
        )

        print(
            "SELL ORDER:",
            symbol
        )

        time.sleep(10)

        try:

            order_info = exchange.fetch_order(
                order['id'],
                symbol
            )

            if (
                order_info['status']
                != 'closed'
            ):

                exchange.cancel_order(
                    order['id'],
                    symbol,
                    {
                        'side': 'sell'
                    }
                )

                print(
                    "SELL CANCELLED:",
                    symbol
                )

                return

        except Exception as e:

            print(
                "SELL CHECK ERROR:",
                str(e)
            )

            return

        profit_percent = (
            (
                sell_price -
                active_trade[
                    "buy_price"
                ]
            )
            /
            active_trade[
                "buy_price"
            ]
        ) * 100

        history.add_trade_history(

            symbol,

            "SELL",

            active_trade[
                "buy_price"
            ],

            sell_price,

            profit_percent

        )

        print(
            "SELL SUCCESS:",
            symbol
        )
        telegram_bot.send_telegram(

            f"🔴 SELL SUCCESS\n\n"
            f"Coin: {symbol}\n"
            f"Sell Price: {sell_price:.8f}\n"
            f"Profit: {profit_percent:.2f}%"

        )

        clear_trade()

    except Exception as e:

        print(
            "SELL ERROR:",
            str(e)
        )


def monitor_trade():

    global active_trade

    try:

        if not active_trade:
            return

        symbol = active_trade[
            "symbol"
        ]

        ticker = exchange.fetch_ticker(
            symbol
        )

        current_price = ticker['last']

        active_trade[
            "current_price"
        ] = round(
            current_price,
            8
        )

        profit_percent = (
            (
                current_price -
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
            profit_percent,
            2
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

        if config.TRAILING_STOP:

            trailing_stop_price = (
                active_trade[
                    "highest_price"
                ]
                *
                (
                    1 -
                    (
                        config.TRAILING_GAP
                        / 100
                    )
                )
            )

            if (
                current_price <
                trailing_stop_price
            ):

                print(
                    "TRAILING STOP HIT"
                )
                telegram_bot.send_telegram(
                    f"⚠️ TRAILING STOP HIT\n\n{symbol}"
                )

                sell_coin()

                return

        if (
            current_price >=
            active_trade[
                "tp_price"
            ]
        ):

            print(
                "TAKE PROFIT HIT"
            )
            telegram_bot.send_telegram(
                f"🎯 TAKE PROFIT HIT\n\n{symbol}"
            )

            sell_coin()

            return

        if (
            current_price <=
            active_trade[
                "sl_price"
            ]
        ):

            print(
                "STOP LOSS HIT"
            )
            telegram_bot.send_telegram(
                f"🛑 STOP LOSS HIT\n\n{symbol}"
            )

            sell_coin()

            return

        save_trade()

    except Exception as e:

        print(
            "MONITOR ERROR:",
            str(e)
        )


def trade_loop():

    global active_trade

    print(
        "TRADER STARTED"
    )

    load_trade()

    while True:

        if not BOT_RUNNING:

            print(
                "TRADER PAUSED"
            )

            time.sleep(5)

            continue

        try:

            if active_trade:

                monitor_trade()

            else:

                for coin in scanner.market_data:

                    signal = coin[
                        "signal"
                    ]

                    symbol = coin[
                        "symbol"
                    ]

                    if signal in [
                        "BUY",
                        "STRONG BUY"
                    ]:

                        buy_coin(
                            symbol
                        )

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
        target=trade_loop
    )

    thread.daemon = True

    thread.start()
