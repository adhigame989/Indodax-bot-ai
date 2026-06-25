import ccxt
import time
import threading
import json
import os
import config
import history
import scanner
import telegram_bot
import uuid

BOT_RUNNING = True
BUY_ENABLED = False
trade_lock = threading.Lock()
exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY,
    'enableRateLimit': True
})

active_trades = []
TRADES_FILE = "/data/active_trades.json"
coin_cooldown = {}

def get_sl_weak_score(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol,
            timeframe=config.TIMEFRAME,
            limit=30
        )

        if not ohlcv:
            return 0

        import pandas as pd
        import ta

        df = pd.DataFrame(
            ohlcv,
            columns=["time","open","high","low","close","volume"]
        )

        close = df["close"]
        volume = df["volume"]

        rsi = ta.momentum.RSIIndicator(close).rsi()
        ema7 = ta.trend.EMAIndicator(close, window=7).ema_indicator()
        ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()

        weak_score = 0

        # volume weakening
        if volume.iloc[-1] < volume.iloc[-2]:
            weak_score += 1

        # EMA weakening
        if ema7.iloc[-1] < ema20.iloc[-1]:
            weak_score += 1

        # RSI weakening
        if rsi.iloc[-1] < rsi.iloc[-2]:
            weak_score += 1

        return weak_score

    except Exception as e:
        print("SL WEAK SCORE ERROR:", str(e))
        return 0
        
def save_trades():
    with open(TRADES_FILE, "w") as f:
        json.dump(active_trades, f, indent=4)
        f.flush()
        os.fsync(f.fileno())

    print(f"SAVED {len(active_trades)} ACTIVE TRADES")

def load_trades():
    global active_trades

    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, "r") as f:
            try:
                data = json.load(f)

                if isinstance(data, list):
                    active_trades.clear()
                    active_trades.extend(data)
                else:
                    active_trades.clear()

            except Exception as e:
                print("LOAD ERROR:", str(e))
                active_trades = []

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

def buy_coin(symbol, signal_type=None, score=None):
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

            unique_symbols = set(
                t["symbol"] for t in active_trades
            )

            if symbol not in unique_symbols and len(unique_symbols) >= config.MAX_ACTIVE_TRADES:
                print(
                    f"MAX COINS REACHED: {len(unique_symbols)}/{config.MAX_ACTIVE_TRADES}"
                )
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
                actual_trade_amount = actual_amount * buy_price

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
                "id": str(uuid.uuid4()),
                "symbol": symbol,
                "buy_price": round(buy_price, 8),
                "current_price": round(buy_price, 8),
                "tp_price": round(tp_price, 8),
                "sl_price": round(sl_price, 8),
                "amount": actual_amount,
                "trade_amount": trade_amount,
                "entry_value": actual_amount * buy_price,
                "highest_price": round(buy_price, 8),
                "lowest_price": round(buy_price, 8),
                "buy_time": time.time(),
                "profit_percent": 0,
                "sl_trigger": False,
                "sl_trigger_time": 0,
                "trailing_trigger": False,
                "trailing_trigger_time": 0,
                "buy_reason": signal_type,
                "buy_score": float(score),
                "tp_mode": False,
                "tp_highest": round(buy_price, 8),
                "timeout_weak_notified": False
            }
            same_coin_count = sum(
                1 for t in active_trades
                if t["symbol"] == symbol)

            if same_coin_count == 0:
                cooldown = 180
            elif same_coin_count == 1:
                cooldown = 300
            else:
                cooldown = 300

            active_trades.append(trade)
            coin_cooldown[symbol] = {"start": time.time(),"duration": cooldown}
            save_trades()

            print("ACTIVE TRADE SAVED:", symbol)
            print("COOLDOWN SET:", symbol)
            print("TOTAL ACTIVE:", len(active_trades))
            print("BUY SUCCESS:", symbol)

            telegram_bot.send_telegram(
                f"🟢 BUY SUCCESS\n\n"
                f"Coin: {symbol}\n"
                f"Modal: Rp {actual_trade_amount:,.0f}\n\n"
                f"Buy Price: Rp {buy_price:,.2f}\n"
                f"TP: Rp {tp_price:,.2f}\n"
                f"SL: Rp {sl_price:,.2f}"
            )

        except Exception as e:
            print("BUY ERROR:", str(e))


def sell_coin(trade, sell_reason=None):

    try:

        if not trade:
            return None
        if trade not in active_trades:
            return None

        symbol = trade["symbol"]

        base_coin = symbol.split("/")[0]

        balance = exchange.fetch_balance()

        wallet_amount = (
            balance["free"].get(base_coin, 0)
            or balance["free"].get(base_coin.lower(), 0)
        )
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
            order_info=exchange.fetch_order(order["id"],symbol)
            filled_amount=float(order_info.get("filled",0))
            remaining_amount=float(order_info.get("remaining",0))

            if filled_amount<=0:
                exchange.cancel_order(order["id"],symbol,{"side":"sell"})
                print("SELL NO FILL:",symbol)
                return None

            if remaining_amount>0:
                exchange.cancel_order(order["id"],symbol,{"side":"sell"})
                print(f"PARTIAL SELL: {symbol} | Filled={filled_amount} | Remaining={remaining_amount}")

            sold_amount=filled_amount
            sell_value=sell_price*sold_amount

            entry_used=(trade["entry_value"]/trade["amount"])*sold_amount
            profit_idr=sell_value-entry_used

            trade["amount"]-=sold_amount
            trade["entry_value"]-=entry_used
            if trade["amount"] <= 0.00000001:
                if trade in active_trades:
                    active_trades.remove(trade)

            save_trades()

        except Exception as e:
            print("SELL CHECK ERROR:", str(e))
            return None

    

        hold_duration = int(
            time.time() - trade.get("buy_time", time.time()))
        profit_percent = (
            (
                sell_price -
                trade["buy_price"]
            )
            /
            trade["buy_price"]
        ) * 100
        if sell_reason == "SL":
            coin_cooldown[symbol] = {
                "start": time.time(),
                "duration": config.SL_COOLDOWN}
            print(f"SL COOLDOWN SET: {symbol}")

        elif sell_reason == "TRAILING":
            coin_cooldown[symbol] = {
                "start": time.time(),
                "duration": config.TRAILING_COOLDOWN}
            print(f"TRAILING COOLDOWN SET: {symbol}")

        pl_label = "Profit"
        if profit_idr < 0:
            pl_label = "Loss"
        history.add_trade_history(
            symbol,
            "SELL",
            trade["buy_price"],
            sell_price,
            profit_percent,
            profit_idr,
            entry_used,
            sell_reason,
            trade.get("buy_reason"),
            trade.get("buy_score"),
            hold_duration
        )

        save_trades()
        print("SELL SUCCESS:", symbol)
        
        result = {
            "sell_price": sell_price,
            "sell_value": sell_value,
            "profit_idr": profit_idr,
            "profit_percent": profit_percent,
            "pl_label": pl_label
        }
        return result

    except Exception as e:

        print("SELL ERROR:", str(e))
        return None

def manual_sell(trade_id):

    try:
        for trade in active_trades[:]:

            if trade["id"] == trade_id:

                symbol = trade["symbol"]

                base_coin = symbol.split("/")[0]

                balance = exchange.fetch_balance()

                wallet_amount = balance["free"].get(
                    base_coin, 0
                )

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

                sell_price = bid_price * (
                    1 - config.SELL_SLIPPAGE
                )

                sell_price = float(
                    exchange.price_to_precision(
                        symbol,
                        sell_price
                    )
                )

                exchange.create_limit_sell_order(
                    symbol,
                    amount,
                    sell_price
                )

                hold_duration = int(
                    time.time() - trade.get("buy_time", time.time()))
                profit_percent = (
                    (
                        sell_price -
                        trade["buy_price"]
                    )
                    /
                    trade["buy_price"]
                ) * 100

                sell_value = (
                    sell_price *
                    float(amount)
                )

                profit_idr = (
                    sell_value -
                    trade["entry_value"]
                )

                pl_label = "Profit"

                if profit_idr < 0:
                    pl_label = "Loss"

                history.add_trade_history(
                    symbol,
                    "SELL",
                    trade["buy_price"],
                    sell_price,
                    profit_percent,
                    profit_idr,
                    trade["entry_value"],
                    "MANUAL",
                    trade.get("buy_reason"),
                    trade.get("buy_score"),
                    hold_duration
                )

                telegram_bot.send_telegram(
                    f"🧾 MANUAL SELL\n\n"
                    f"Coin: {symbol}\n"
                    f"Nilai Jual: Rp {sell_value:,.0f}\n"
                    f"Sell Price: Rp {sell_price:,.2f}\n"
                    f"{pl_label}: Rp {profit_idr:,.0f} ({profit_percent:.2f}%)"
                )

                active_trades.remove(trade)
                save_trades()

                print("MANUAL SELL:", symbol)

                return True

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
        
        btc_status = scanner.check_btc_market()

        if btc_status == "PANIC":
            hold_hours = (time.time() - trade["buy_time"]) / 3600
            weak_score = 0

            if profit_percent < 0:
                weak_score += 1
            if profit_percent <= config.BTC_PANIC_DEEP_LOSS:
                weak_score += 1
            if current_price < trade["buy_price"]:
                weak_score += 1
            if hold_hours > config.BTC_PANIC_HOLD_HOURS:
                weak_score += 1
            if weak_score >= config.BTC_PANIC_EXIT_SCORE:
                print("BTC PANIC WEAK EXIT:", symbol)

                result = sell_coin(trade,"BTC_PANIC_EXIT")

                if result:
                    telegram_bot.send_telegram(
                        f"⚠ BTC PANIC EXIT\n\n"
                        f"Coin: {symbol}\n"
                        f"Weak Score: {weak_score}/3\n"
                        f"Sell Price: Rp {result['sell_price']:,.2f}\n"
                        f"Hasil Jual: Rp {result['sell_value']:,.0f}\n"
                        f"{result['pl_label']}: Rp {abs(result['profit_idr']):,.0f} ({result['profit_percent']:.2f}%)"
                    )

                return

        if current_price > trade["highest_price"]:
            trade["highest_price"] = current_price

        if current_price < trade["lowest_price"]:
            trade["lowest_price"] = current_price

        # Smart trailing aktif setelah profit cukup
        if (config.TRAILING_STOP
            and profit_percent >= config.TRAILING_START
        and not trade["tp_mode"]):

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
                        f"📉 TRAILING TOUCHED\n\n"
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

                    locked_profit = ((current_price -trade["buy_price"]
                        )/trade["buy_price"]) * 100

                    if locked_profit < config.MIN_LOCK_PROFIT:
                        print(f"TRAILING HOLD: {symbol} | locked {locked_profit:.2f}% < {config.MIN_LOCK_PROFIT}%")
                        return
                        
                    print("TRAILING SELL:", symbol)
                    result = sell_coin(trade,"TRAILING")
                    if result:
                        telegram_bot.send_telegram(
                            f"🪙 TRAILING SELL\n\n"
                            f"Coin: {symbol}\n"
                            f"Sell Price: Rp {result['sell_price']:,.2f}\n"
                            f"Hasil Jual: Rp {result['sell_value']:,.0f}\n"
                            f"Profit: Rp {result['profit_idr']:,.0f} ({result['profit_percent']:.2f}%)"
                        )

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

            print("TP ZONE:", symbol)
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

                real_bid = ticker["bid"]

                tp_gap = ((current_price - real_bid)/ current_price) * 100
                real_bid_profit = ((real_bid - trade["buy_price"])/ trade["buy_price"]) * 100

                if tp_gap > config.MAX_TP_GAP:

                    print(
                        f"TP GAP TOO WIDE: {symbol} | "
                        f"Last={current_price} "
                        f"Bid={real_bid} "
                        f"Gap={tp_gap:.2f}%"
                    )

                    telegram_bot.send_telegram(
                        f"⚠️ TP FAKE PUMP HOLD\n\n"
                        f"Coin: {symbol}\n"
                        f"Chart: {profit_percent:.2f}%\n"
                        f"Gap: {tp_gap:.2f}%\n"
                        f"Status: Hold"
                    )

                    return

                if real_bid_profit < config.MIN_LOCK_PROFIT:

                    print(
                        f"TP LOCK TOO LOW: {symbol} | "
                        f"BidProfit={real_bid_profit:.2f}%")

                    telegram_bot.send_telegram(
                        f"⚠️ TP HOLD (LOW LOCK)\n\n"
                        f"Coin: {symbol}\n"
                        f"Chart: {profit_percent:.2f}%\n"
                        f"Real Bid: {real_bid_profit:.2f}%\n"
                        f"Min Lock: {config.MIN_LOCK_PROFIT:.2f}%"
                    )

                    return

                print("TP SELL:", symbol)

                result = sell_coin(trade, "TP")

                if result:
                    telegram_bot.send_telegram(
                        f"🚀 TP CONFIRM SELL\n\n"
                        f"Coin: {symbol}\n"
                        f"Sell Price: Rp {result['sell_price']:,.2f}\n"
                        f"Hasil Jual: Rp {result['sell_value']:,.0f}\n"
                        f"Profit: Rp {result['profit_idr']:,.0f} ({result['profit_percent']:.2f}%)"
                    )

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

        panic_sl_price = trade["sl_price"]

        if btc_status == "PANIC":
            panic_sl_price = (trade["buy_price"] *(1 - ((config.STOP_LOSS / 2) / 100)))

        if current_price <= panic_sl_price:

            if not trade["sl_trigger"]:

                trade["sl_trigger"] = True

                trade["sl_trigger_time"] = time.time()

                print("SL TOUCHED:", symbol)
                telegram_bot.send_telegram(
                    f"🚨 SL TOUCHED\n\n"
                    f"Coin: {symbol}\n"
                    f"Price: Rp {current_price:,.2f}\n"
                    f"Buffer: 60 sec started"
                )

                save_trades()

                print("SL TRIGGER:",symbol)

                return

            if (time.time()-trade["sl_trigger_time"]>= 60):

                hold_hours = (time.time() - trade["buy_time"]) / 3600
                weak_score = get_sl_weak_score(symbol)
                if profit_percent < 0:
                    weak_score += 1

                if profit_percent <= config.TIMEOUT_DEEP_LOSS:
                    weak_score += 1

                if hold_hours >= config.TIMEOUT_HARD_HOURS:
                    weak_score += 1

                stop_loss_percent = ((trade["buy_price"] -trade["sl_price"])
                    /trade["buy_price"]) * 100

                emergency_sl = stop_loss_percent + config.EMERGENCY_SL_EXTRA

                current_loss = ((trade["buy_price"] -current_price)
                    /trade["buy_price"]) * 100

    # Emergency SL
                if current_loss >= emergency_sl:

                    print("EMERGENCY SL:", symbol)

                    result = sell_coin(trade, "SL_EMERGENCY")

                    if result:
                        telegram_bot.send_telegram(
                            f"🚨 EMERGENCY SL SELL\n\n"
                            f"Coin: {symbol}\n"
                            f"Sell Price: Rp {result['sell_price']:,.2f}\n"
                            f"Hasil Jual: Rp {result['sell_value']:,.0f}\n"
                            f"{result['pl_label']}: Rp {abs(result['profit_idr']):,.0f} ({result['profit_percent']:.2f}%)"
                        )
                            
                    return

    # Smart SL Confirm
                if weak_score >= config.TIMEOUT_EXIT_SCORE:

                    print("SMART SL SELL:", symbol)

                    result = sell_coin(trade, "SL")

                    if result:
                        telegram_bot.send_telegram(
                            f"💸 SMART SL SELL\n\n"
                            f"Coin: {symbol}\n"
                            f"Weak Score: {weak_score}/3\n"
                            f"Sell Price: Rp {result['sell_price']:,.2f}\n"
                            f"Hasil Jual: Rp {result['sell_value']:,.0f}\n"
                            f"{result['pl_label']}: Rp {abs(result['profit_idr']):,.0f} ({result['profit_percent']:.2f}%)"
                        )

                    return

    # Recovery hold
                trade["sl_trigger"] = False
                trade["sl_trigger_time"] = 0

                print("SL HOLD RECOVERY:", symbol)
                telegram_bot.send_telegram(
                    f"🛡️ SL HOLD RECOVERY\n\n"
                    f"Coin: {symbol}\n"
                    f"Weak Score: {weak_score}/3\n"
                    f"Loss: -{current_loss:.2f}%\n"
                    f"Status: Recovery Hold"
                )

        save_trades()
        # TIMEOUT WEAK
        hold_seconds = (
            time.time()
            -
            trade.get("buy_time", time.time()))

        hold_hours = hold_seconds / 3600

        current_profit = trade.get("profit_percent",0)

        if (
            hold_hours >= config.TIMEOUT_WEAK_HOURS
            and current_profit < config.TIMEOUT_WEAK_PROFIT):

            weak_score = get_sl_weak_score(symbol)

            if weak_score >= config.TIMEOUT_EXIT_SCORE:
                
                print("TIMEOUT WEAK SELL:", symbol)

                result = sell_coin(trade,"TIMEOUT_WEAK")

                if result:

                    telegram_bot.send_telegram(
                        f"⏱ TIMEOUT WEAK SELL\n\n"
                        f"Coin: {symbol}\n"
                        f"Hold: {hold_hours:.1f}h\n"
                        f"Weak Score: {weak_score}/3\n"
                        f"Sell Price: Rp {result['sell_price']:,.2f}\n"
                        f"Hasil Jual: Rp {result['sell_value']:,.0f}\n"
                        f"{result['pl_label']}: Rp {abs(result['profit_idr']):,.0f} ({result['profit_percent']:.2f}%)"
                    )
            else:

                if not trade.get("timeout_weak_notified", False):
                    print("TIMEOUT WEAK HOLD:", symbol)

                    telegram_bot.send_telegram(
                        f"⏳ TIMEOUT WEAK HOLD\n\n"
                        f"Coin: {symbol}\n"
                        f"Hold: {hold_hours:.1f}h\n"
                        f"Weak Score: {weak_score}/3\n"
                        f"Profit: {current_profit:.2f}%\n"
                        f"Status: Continue Holding"
                    )
                    trade["timeout_weak_notified"] = True
                    save_trades()

            return

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

            from collections import Counter

            unique_symbols = set(t["symbol"] for t in active_trades)

            layer_counts = Counter(t["symbol"] for t in active_trades)

            print("ACTIVE:",len(unique_symbols),"/",config.MAX_ACTIVE_TRADES)

            for symbol, count in layer_counts.items():
                print(f"{symbol} Layer {count}/{config.MAX_LAYER_PER_COIN}")
            for coin in scanner.market_data[:]:
                signal = coin["signal"]
                symbol = coin["symbol"]
                score = coin["score"]

                same_coin_count = sum(
                    1 for t in active_trades
                    if t["symbol"] == symbol
                )
                now = time.time()

                if same_coin_count == 0:
                    cooldown = 0
                elif same_coin_count == 1:
                    cooldown = 180
                elif same_coin_count == 2:
                    cooldown = 300
                else:
                    cooldown = 300

                if symbol in coin_cooldown:

                    cooldown_data = coin_cooldown[symbol]

                    cooldown_age = (now -cooldown_data["start"])

                    cooldown = cooldown_data["duration"]

                    if cooldown_age < cooldown:
                        print(f"COOLDOWN SKIP: {symbol}")

                        continue
                    else:
                        del coin_cooldown[symbol]

                print(
                    f"{symbol} | signal={signal} | layers={same_coin_count} | cooldown={cooldown}"
                )
                unique_symbols = set(
                    t["symbol"] for t in active_trades
                )

                if same_coin_count >= config.MAX_LAYER_PER_COIN:
                    continue

                if (
                    symbol not in unique_symbols
                    and len(unique_symbols) >= config.MAX_ACTIVE_TRADES
                ):
                    continue

                if BUY_ENABLED:
                    btc_status = scanner.check_btc_market()

                    if btc_status == "PANIC" and same_coin_count > 0:
                        print(f"BTC PANIC - LAYER BLOCKED: {symbol}")
                        continue

    # Layer 1
                    if same_coin_count == 0:

                        if signal in ["BUY", "STRONG BUY"]:
                            buy_coin(symbol, signal, score)
                            break

    # Layer 2
                    elif same_coin_count == 1:

                        if (
                            signal in ["BUY", "STRONG BUY"]
                            and score >= 80
                        ):
                            buy_coin(symbol, signal, score)
                            break

    # Layer 3
                    elif same_coin_count == 2:

                        if (
                            signal == "STRONG BUY"
                            and score >= 95
                        ):
                            buy_coin(symbol, signal, score)
                            break

        except Exception as e:

            print("TRADER ERROR:", str(e))

        time.sleep(
            config.TRADER_INTERVAL
        )

def start_trader():

    print("STARTING TRADER THREAD")

    thread = threading.Thread(
        target=trade_loop
    )

    thread.daemon = True
    thread.start()
