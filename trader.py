import ccxt
import time
import threading
import json
import os
import config
import history
import scanner
import telegram_bot
import json
import os

BOT_RUNNING = False
trade_lock = threading.Lock()
exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trades = []
TRADES_FILE = "active_trades.json"
coin_cooldown = {}

def save_trades():

    with open(TRADES_FILE, "w") as f:
        json.dump(active_trades, f, indent=4)


def load_trades():

    global active_trades

    if os.path.exists(TRADES_FILE):

        with open(TRADES_FILE, "r") as f:
            active_trades = json.load(f)

        print(
            f"LOADED {len(active_trades)} ACTIVE TRADES"
        )

def get_trade_amount(balance):

    try:

        effective_balance = min(balance,config.BOT_CAPITAL_LIMIT)

        compound_size = (effective_balance *(config.COMPOUND_PERCENT / 100))

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

        print("TRADE AMOUNT ERROR:", str(e))

        return config.BASE_TRADE_AMOUNT

def buy_coin(symbol):
    global active_trades

    with trade_lock:
        try:
            same_coin_count = sum(
                1 for t in active_trades
                if t["symbol"] == symbol
            )

            if same_coin_count >= config.MAX_LAYER_PER_COIN:
                print(
                    f"MAX LAYER REACHED: {symbol}"
                )
                return

            if len(active_trades) >= config.MAX_ACTIVE_TRADES:
                print(f"MAX TRADE REACHED: {len(active_trades)}/{config.MAX_ACTIVE_TRADES}")
                return

            balance = exchange.fetch_balance()
            idr = balance["free"].get("IDR", 0)
            trade_amount = get_trade_amount(idr)

            if idr < trade_amount:
                print("NOT ENOUGH IDR")
                return

            ticker = exchange.fetch_ticker(symbol)
            ask_price = ticker["ask"]

            buy_price = ask_price * (1 + config.BUY_SLIPPAGE)

            amount = trade_amount / buy_price

            amount_precise = float(exchange.amount_to_precision(symbol,amount))
            if amount_precise >= 1:
                amount = int(amount_precise)
            else:
                amount = amount_precise
            buy_price = float(exchange.price_to_precision(symbol, buy_price))

            print("BUY SYMBOL:", symbol)
            print("TRADE AMOUNT:", trade_amount)
            print("BUY PRICE:", buy_price)
            print("AMOUNT:", amount)

            order = exchange.create_limit_buy_order(
                symbol,
                amount,
                buy_price
            )

            print("BUY ORDER:", symbol)

            time.sleep(10)

            try:
                order_info = exchange.fetch_order(
                    order["id"],
                    symbol
                )

                base_coin = symbol.split("/")[0].lower()
                receive_key = f"receive_{base_coin}"

                actual_amount = float(
                    order_info["info"]["return"]["order"].get(
                        receive_key,
                        amount
                    )
                )

                print("ACTUAL AMOUNT:", actual_amount)

                if order_info["status"] != "closed":
                    exchange.cancel_order(
                        order["id"],
                        symbol,
                        {"side": "buy"}
                    )

                    print("BUY CANCELLED:", symbol)
                    return

            except Exception as e:
                print("BUY CHECK ERROR:", str(e))
                return

            tp_price = buy_price * (1 + (config.TAKE_PROFIT / 100))
            sl_price = buy_price * (1 - (config.STOP_LOSS / 100))

            trade = {
                "symbol": symbol,
                "buy_price": round(buy_price, 8),
                "current_price": round(buy_price, 8),
                "tp_price": round(tp_price, 8),
                "sl_price": round(sl_price, 8),
                "amount": actual_amount,
                "trade_amount": trade_amount,
                "entry_value": trade_amount,
                "highest_price": round(buy_price, 8),
                "lowest_price": round(buy_price, 8),
                "buy_time": time.time(),
                "profit_percent": 0,
                "sl_trigger": False,
                "sl_trigger_time": 0,
                "trailing_trigger": False,
                "trailing_trigger_time": 0,
                "tp_mode": False,
                "tp_highest": round(buy_price, 8)
            }

            active_trades.append(trade)
            save_trades()

            print("ACTIVE TRADES SAVED:", len(active_trades))

            save_trades()

            print("BUY SUCCESS:", symbol)

            telegram_bot.send_telegram(
                f"🟢 BUY SUCCESS\n\n"
                f"Coin: {symbol}\n"
                f"Modal: Rp {trade_amount:,.0f}\n\n"
                f"Buy Price: Rp {buy_price:,.2f}\n"
                f"TP: Rp {tp_price:,.2f}\n"
                f"SL: Rp {sl_price:,.2f}"
            )

        except Exception as e:
            print("BUY ERROR:", str(e))


def sell_coin(trade):

    try:

        if not trade:
            return

        symbol = trade["symbol"]

        base_coin = symbol.split("/")[0]

        balance = exchange.fetch_balance()

        wallet_amount = balance['free'].get(base_coin,0)

        if wallet_amount <= 0:
            print(
                f"{symbol} already sold, cleaning trade"
            )

            if trade in active_trades:
                active_trades.remove(trade)
                save_trades()

            return

        amount = min(
            trade["amount"],
            wallet_amount
        )

        amount = exchange.amount_to_precision(
            symbol,
            amount
        )

        ticker = exchange.fetch_ticker(symbol)

        bid_price = ticker['bid']

        sell_price = (bid_price *(1 - config.SELL_SLIPPAGE))

        sell_price = float(exchange.price_to_precision(symbol,sell_price))

        print(
            f"SELL AMOUNT: "
            f"{amount} / "
            f"WALLET: {wallet_amount}"
        )

        order = exchange.create_limit_sell_order(
            symbol,
            amount,
            sell_price
        )

        print("SELL ORDER:", symbol)

        time.sleep(10)

        try:

            order_info = exchange.fetch_order(
                order['id'],
                symbol
            )

            if order_info['status'] != 'closed':

                exchange.cancel_order(
                    order['id'],
                    symbol,
                    {'side': 'sell'}
                )

                print("SELL CANCELLED:", symbol)
                return

        except Exception as e:

            print("SELL CHECK ERROR:", str(e))
            return

        profit_percent = (
            (
                sell_price -
                trade["buy_price"]
            )
            /
            trade["buy_price"]
        ) * 100
        if profit_percent < 0:
            coin_cooldown[symbol] = time.time()
            print("COOLDOWN SET:", symbol)

        sell_value = sell_price * amount

        profit_idr = (
            sell_value -
            trade["entry_value"]
        )
        history.add_trade_history(
            symbol,
            "SELL",
            trade["buy_price"],
            sell_price,
            profit_percent
        )

        print("SELL SUCCESS:", symbol)

        telegram_bot.send_telegram(
            f"🔴 SELL SUCCESS\n\n"
            f"Coin: {symbol}\n"
            f"Nilai Jual: Rp {sell_value:,.0f}\n"
            f"Sell Price: Rp {sell_price:,.2f}\n"
            f"Profit: Rp {profit_idr:,.0f} ({profit_percent:.2f}%)"
        )

        if trade in active_trades:

            active_trades.remove(
                trade
            )
        save_trades()

        if active_trades:
            active_trade = active_trades[0]
        else:
            active_trade = None

    except Exception as e:

        print("SELL ERROR:", str(e))

def manual_sell(symbol):

    try:
        for trade in active_trades:
            if trade["symbol"] == symbol:

                base_coin = symbol.split("/")[0]

                balance = exchange.fetch_balance()
                wallet_amount = balance["free"].get(base_coin, 0)

                amount = min(
                    trade["amount"],
                    wallet_amount
                )

                amount = exchange.amount_to_precision(
                    symbol,
                    amount
                )
                
                ticker = exchange.fetch_ticker(symbol)

                bid_price = ticker["bid"]

                sell_price = (
                    bid_price *
                    (1 - config.SELL_SLIPPAGE)
                )
                sell_price = float(exchange.price_to_precision(symbol, sell_price))
                
                exchange.create_limit_sell_order(
                    symbol,
                    amount,
                    sell_price
                )

                profit_percent = (
                    (
                        sell_price -
                        trade["buy_price"]
                    )
                    /
                    trade["buy_price"]
                ) * 100

                sell_value = sell_price * amount

                profit_idr = (
                    sell_value -
                    trade["entry_value"]
                )

                history.add_trade_history(
                    symbol,
                    "MANUAL SELL",
                    trade["buy_price"],
                    sell_price,
                    profit_percent
                )

                telegram_bot.send_telegram(
                    f"⚠️ MANUAL SELL\n\n"
                    f"Coin: {symbol}\n"
                    f"Sell Price: Rp {sell_price:,.2f}\n"
                    f"Profit: Rp {profit_idr:,.0f} ({profit_percent:.2f}%)"
                )

                active_trades.remove(trade)
                save_trades()

                if active_trades:
                    active_trade = active_trades[0]
                else:
                    active_trade = None

                print("MANUAL SELL:", symbol)

                break

    except Exception as e:
        print("MANUAL SELL ERROR:", str(e))
def monitor_trade(trade):

    try:

        if not trade:
            return

        symbol = trade["symbol"]

        ticker = exchange.fetch_ticker(symbol)

        current_price = ticker['last']

        trade["current_price"] = round(
            current_price,
            8
        )
        trade["current_value"] = (
            current_price *
            trade["amount"]
        )

        profit_percent = (
            (
                current_price -
                trade["buy_price"]
            )
            /
            trade["buy_price"]
        ) * 100

        trade["profit_percent"] = round(
            profit_percent,
            2
        )

        if current_price > trade["highest_price"]:
            trade["highest_price"] = current_price

        if current_price < trade["lowest_price"]:
            trade["lowest_price"] = current_price

        # Smart trailing aktif setelah profit cukup
        if (config.TRAILING_STOP
            and profit_percent >= config.TRAILING_START
        ):

            trailing_stop_price = (
                trade["highest_price"]
                *
                (
                    1 - (
                        config.TRAILING_GAP / 100
                    )
                )
            )

            if current_price <= trailing_stop_price:

                if not trade["trailing_trigger"]:

                    trade["trailing_trigger"] = True
                    trade["trailing_trigger_time"] = time.time()

                    telegram_bot.send_telegram(
                        f"⚠️ TRAILING TOUCHED\n\n"
                        f"Coin: {symbol}\n"
                        f"Price: Rp {current_price:,.2f}\n"
                        f"Buffer: 30 sec started"
                    )

                    save_trades()

                    print(
                        "TRAILING TRIGGER:",
                        symbol
                    )

                    return

                if (
                    time.time()
                    -
                    trade["trailing_trigger_time"]
                    >= 30
                ):

                    telegram_bot.send_telegram(
                        f"🎯 TRAILING SELL\n\n"
                        f"Coin: {symbol}\n"
                        f"Profit secured"
                    )

                    sell_coin(trade)

                    return

            else:

                if trade["trailing_trigger"]:

                    trade["trailing_trigger"] = False
                    trade["trailing_trigger_time"] = 0

                    telegram_bot.send_telegram(
                        f"✅ TRAILING RECOVERED\n\n"
                        f"Coin: {symbol}\n"
                        f"Price back above trailing"
                    )

                    save_trades()
        # Dynamic TP Buffer
        tp_buffer_percent = (
            config.TAKE_PROFIT *
            (1 - config.TP_BUFFER_RATIO)
        )

        # Masuk profit zone
        if (
            profit_percent >= tp_buffer_percent
            and not trade["tp_mode"]
        ):

            trade["tp_mode"] = True
            trade["tp_highest"] = current_price

            telegram_bot.send_telegram(
                f"🎯 TP ZONE ENTERED\n\n"
                f"Coin: {symbol}\n"
                f"Profit: {profit_percent:.2f}%"
            )

            save_trades()

        # TP Confirmation Mode
        if trade["tp_mode"]:

            if current_price > trade["tp_highest"]:
                trade["tp_highest"] = current_price

            tp_trailing_price = (
                trade["tp_highest"]
                *
                (
                    1 - (
                        config.TP_CONFIRM_TRAILING / 100
                    )
                )
            )

            if current_price <= tp_trailing_price:

                telegram_bot.send_telegram(
                    f"🚀 TP CONFIRM SELL\n\n"
                    f"Coin: {symbol}\n"
                    f"Profit locked"
                )

                sell_coin(trade)

                return
        if trade["sl_trigger"]:

            if current_price > trade["sl_price"]:

                trade["sl_trigger"] = False

                trade["sl_trigger_time"] = 0
                telegram_bot.send_telegram(
                    f"✅ SL RECOVERED\n\n"
                    f"Coin: {symbol}\n"
                    f"Price back above SL"
                )

                save_trades()

                print(
                    "PRICE RECOVERED:",
                    symbol
                )
                return

        if current_price <= trade["sl_price"]:

            if not trade["sl_trigger"]:

                trade["sl_trigger"] = True

                trade["sl_trigger_time"] = time.time()

                telegram_bot.send_telegram(
                    f"⚠️ SL TOUCHED\n\n"
                    f"Coin: {symbol}\n"
                    f"Price: Rp {current_price:,.2f}\n"
                    f"Buffer: 60 sec started"
                )

                save_trades()

                print(
                    "SL TRIGGER:",
                    symbol
                )

                return

            if (
                time.time()
                -
                trade["sl_trigger_time"]
                >= 60
            ):

                telegram_bot.send_telegram(
                    f"🛑 STOP LOSS HIT\n\n{symbol}"
                )

                sell_coin(trade)

                return

        save_trades()

    except Exception as e:

        print("MONITOR ERROR:", str(e))


def trade_loop():

    print("TRADER STARTED")

    while True:

        if not BOT_RUNNING:

            print("TRADER PAUSED")

            time.sleep(5)
            continue

        try:

            for trade in active_trades[:]:

                monitor_trade(trade)

            print(
                "ACTIVE:",len(active_trades),"/",config.MAX_ACTIVE_TRADES)
            if len(active_trades) < config.MAX_ACTIVE_TRADES:

                for coin in scanner.market_data:

                    signal = coin["signal"]
                    symbol = coin["symbol"]
                    if symbol in coin_cooldown:

                        cooldown_age = (
                            time.time()
                            - coin_cooldown[symbol]
                    )

                        if cooldown_age < 1800:

                            print(f"COOLDOWN SKIP: {symbol}")

                            continue

                    if signal in [
                        "BUY",
                        "STRONG BUY"
                    ]:

                        buy_coin(symbol)
                        break

        except Exception as e:

            print("TRADER ERROR:", str(e))

        time.sleep(
            config.TRADER_INTERVAL
        )
load_trades()

def start_trader():

    print("STARTING TRADER THREAD")

    thread = threading.Thread(
        target=trade_loop
    )

    thread.daemon = True
    thread.start()
