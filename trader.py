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

# ACTIVE POSITION
active_trade = None


def get_idr_balance():

    try:

        balance = exchange.fetch_balance()

        idr = balance['total'].get('IDR', 0)

        return float(idr)

    except Exception as e:

        print("BALANCE ERROR:", str(e))

        return 0


def buy_coin(symbol, buy_price):

    try:

        # cek saldo IDR
        idr_balance = get_idr_balance()

        print("IDR BALANCE:", idr_balance)

        if idr_balance < config.BASE_TRADE_AMOUNT:

            print("NOT ENOUGH IDR")

            return None

        # jumlah coin
        amount = (
            config.BASE_TRADE_AMOUNT
            / buy_price
        )

        # precision aman
        amount = round(amount, 8)

        # slippage buy
        buy_price = buy_price * (
            1 + config.BUY_SLIPPAGE
        )

        # rounding
        buy_price = round(buy_price, 8)

        print(
            "BUY ORDER:",
            symbol,
            amount,
            buy_price
        )

        # LIMIT BUY
        order = exchange.create_order(
            symbol=symbol,
            type="limit",
            side="buy",
            amount=amount,
            price=buy_price
        )

        print("BUY SUCCESS:", order)

        return {
            "amount": amount,
            "order": order,
            "buy_price": buy_price
        }

    except Exception as e:

        print("BUY ERROR:", str(e))

        return None


def sell_coin(symbol, amount, sell_price):

    try:

        # precision aman
        amount = round(amount, 8)

        # slippage sell
        sell_price = sell_price * (
            1 - config.SELL_SLIPPAGE
        )

        # rounding
        sell_price = round(sell_price, 8)

        print(
            "SELL ORDER:",
            symbol,
            amount,
            sell_price
        )

        # LIMIT SELL
        order = exchange.create_order(
            symbol=symbol,
            type="limit",
            side="sell",
            amount=amount,
            price=sell_price
        )

        print("SELL SUCCESS:", order)

        return order

    except Exception as e:

        print("SELL ERROR:", str(e))

        return None


def trader_loop():

    global active_trade

    print("TRADER STARTED")

    while True:

        try:

            market_data = scanner.market_data

            print(
                "MARKET DATA LENGTH:",
                len(market_data)
            )

            # ===================================
            # ENTRY
            # ===================================

            if active_trade is None:

                print("SEARCHING ENTRY...")

                for coin in market_data:

                    print(
                        "CHECK:",
                        coin["symbol"],
                        coin["signal"],
                        coin["score"]
                    )

                    # hanya BUY
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

                    # BUY SUCCESS
                    if buy_result:

                        amount = buy_result["amount"]

                        real_buy_price = (
                            buy_result["buy_price"]
                        )

                        tp_price = real_buy_price * (
                            1 +
                            config.TAKE_PROFIT / 100
                        )

                        sl_price = real_buy_price * (
                            1 -
                            config.STOP_LOSS / 100
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

                        print(
                            "ACTIVE TRADE:",
                            active_trade
                        )

                        break

            # ===================================
            # MONITOR POSITION
            # ===================================

            else:

                print(
                    "MONITORING:",
                    active_trade["symbol"]
                )

                for coin in market_data:

                    if (
                        coin["symbol"] !=
                        active_trade["symbol"]
                    ):
                        continue

                    current_price = float(
                        coin["price"]
                    )

                    active_trade[
                        "current_price"
                    ] = current_price

                    # PROFIT %
                    profit = (
                        (
                            current_price -
                            active_trade["buy_price"]
                        )
                        /
                        active_trade["buy_price"]
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

                    # UPDATE HIGHEST
                    if (
                        current_price >
                        active_trade["highest_price"]
                    ):

                        active_trade[
                            "highest_price"
                        ] = current_price

                    # TRAILING PRICE
                    trailing_price = (
                        active_trade["highest_price"]
                        *
                        (
                            1 -
                            config.TRAILING_GAP / 100
                        )
                    )

                    # ===================================
                    # TAKE PROFIT
                    # ===================================

                    if (
                        current_price >=
                        active_trade["tp_price"]
                    ):

                        print(
                            "TAKE PROFIT HIT"
                        )

                        sell_result = sell_coin(
                            active_trade["symbol"],
                            active_trade["amount"],
                            current_price
                        )

                        if sell_result:

                            print(
                                "TP SELL SUCCESS"
                            )

                            active_trade = None

                        break

                    # ===================================
                    # STOP LOSS
                    # ===================================

                    elif (
                        current_price <=
                        active_trade["sl_price"]
                    ):

                        print(
                            "STOP LOSS HIT"
                        )

                        sell_result = sell_coin(
                            active_trade["symbol"],
                            active_trade["amount"],
                            current_price
                        )

                        if sell_result:

                            print(
                                "SL SELL SUCCESS"
                            )

                            active_trade = None

                        break

                    # ===================================
                    # TRAILING STOP
                    # ===================================

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
                            active_trade["symbol"],
                            active_trade["amount"],
                            current_price
                        )

                        if sell_result:

                            print(
                                "TRAILING SELL SUCCESS"
                            )

                            active_trade = None

                        break

        except Exception as e:

            print(
                "TRADER ERROR:",
                str(e)
            )

        time.sleep(15)


def start_trader():

    print("STARTING TRADER THREAD")

    thread = threading.Thread(
        target=trader_loop
    )

    thread.daemon = True

    thread.start()
