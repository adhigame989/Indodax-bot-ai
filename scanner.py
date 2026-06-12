import ccxt
import threading
import time
import pandas as pd
import ta
import config

BOT_RUNNING = False

exchange = ccxt.indodax({
    "enableRateLimit": True
})

market_data = []
recent_logs = []

BLACKLIST = [
    "USDT/IDR",
    "USDC/IDR",
    "FDUSD/IDR",
    "TUSD/IDR",
    "BUSD/IDR"
]

def get_volume_acceleration_score(latest_volume, avg_volume):

    if avg_volume <= 0:
        return 0

    ratio = latest_volume / avg_volume

    if ratio >= 4:
        return 35

    if ratio >= 3:
        return 25

    if ratio >= 2:
        return 15

    if ratio >= 1.5:
        return 8

    if ratio < 0.8:
        return -10

    return 0


def get_multi_tf_score(symbol):

    try:

        score_15m = 0
        score_1h = 0
        score_4h = 0

        tf_15m = exchange.fetch_ohlcv(
            symbol,
            timeframe="15m",
            limit=60
        )

        tf_1h = exchange.fetch_ohlcv(
            symbol,
            timeframe="1h",
            limit=60
        )

        tf_4h = exchange.fetch_ohlcv(
            symbol,
            timeframe="4h",
            limit=60
        )

        if not tf_15m or not tf_1h or not tf_4h:
            return 0

        df_15m = pd.DataFrame(
            tf_15m,
            columns=["time","open","high","low","close","volume"]
        )

        df_1h = pd.DataFrame(
            tf_1h,
            columns=["time","open","high","low","close","volume"]
        )

        df_4h = pd.DataFrame(
            tf_4h,
            columns=["time","open","high","low","close","volume"]
        )

        close_15m = df_15m["close"]
        close_1h = df_1h["close"]
        close_4h = df_4h["close"]

        rsi_15m = ta.momentum.RSIIndicator(close_15m).rsi()
        ema20_15m = ta.trend.EMAIndicator(close_15m, window=20).ema_indicator()
        ema50_15m = ta.trend.EMAIndicator(close_15m, window=50).ema_indicator()

        if ema20_15m.iloc[-1] > ema50_15m.iloc[-1]:
            score_15m += 40

        if close_15m.iloc[-1] > ema20_15m.iloc[-1]:
            score_15m += 30

        if 40 <= rsi_15m.iloc[-1] <= 75:
            score_15m += 30

        rsi_1h = ta.momentum.RSIIndicator(close_1h).rsi()
        ema20_1h = ta.trend.EMAIndicator(close_1h, window=20).ema_indicator()
        ema50_1h = ta.trend.EMAIndicator(close_1h, window=50).ema_indicator()

        if ema20_1h.iloc[-1] > ema50_1h.iloc[-1]:
            score_1h += 40

        if close_1h.iloc[-1] > ema20_1h.iloc[-1]:
            score_1h += 30

        if 40 <= rsi_1h.iloc[-1] <= 75:
            score_1h += 30

        ema20_4h = ta.trend.EMAIndicator(close_4h, window=20).ema_indicator()
        ema50_4h = ta.trend.EMAIndicator(close_4h, window=50).ema_indicator()

        if ema20_4h.iloc[-1] > ema50_4h.iloc[-1]:
            score_4h += 20

        final_score = (
            score_15m +
            score_1h +
            score_4h
        ) / 2.2

        return round(final_score, 2)

    except Exception as e:

        print("MULTI TF ERROR:", symbol, str(e))
        return 0


def check_btc_market():

    try:

        ohlcv = exchange.fetch_ohlcv(
            "BTC/IDR",
            timeframe="1h",
            limit=100
        )

        if not ohlcv:
            return "NEUTRAL"

        df = pd.DataFrame(
            ohlcv,
            columns=["time","open","high","low","close","volume"]
        )

        close = df["close"]

        rsi = ta.momentum.RSIIndicator(close).rsi()
        ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()

        latest_price = close.iloc[-1]
        latest_open = df["open"].iloc[-1]

        btc_change = (
            (latest_price - latest_open)
            / latest_open
        ) * 100

        if btc_change <= -3 or rsi.iloc[-1] < 35:
            return "PANIC"

        if rsi.iloc[-1] > 55 and ema20.iloc[-1] > ema50.iloc[-1]:
            return "BULLISH"

        return "NEUTRAL"

    except Exception as e:

        print("BTC FILTER ERROR:", str(e))
        return "NEUTRAL"


def build_market_universe(tickers):

    candidates = []

    for symbol in tickers:

        try:

            if "/IDR" not in symbol:
                continue

            if symbol == "BTC/IDR":
                continue

            if symbol in BLACKLIST:
                continue

            data = tickers[symbol]

            volume = data.get("quoteVolume", 0)
            bid = data.get("bid", 0)
            ask = data.get("ask", 0)
            percentage = data.get("percentage", 0)

            if not volume or not bid or not ask:
                continue

            if volume < config.MIN_VOLUME:
                continue

            spread = ((ask - bid) / ask) * 100

            if (
                config.ENABLE_SPREAD_FILTER
                and spread > config.MAX_SPREAD
            ):
                continue

            score = 0

            if percentage and percentage > 0:
                score += percentage * 2

            score += volume / config.MIN_VOLUME

            if spread < 0.5:
                score += 15

            if volume > (config.MIN_VOLUME * 5):
                score += 20

            candidates.append({
                "symbol": symbol,
                "score": score,
                "volume": volume
            })

        except Exception:
            continue

    candidates = sorted(
        candidates,
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[:config.SCAN_LIMIT]


def scan_market():

    global market_data

    print("SCANNER STARTED")

    while True:

        if not BOT_RUNNING:

            print("SCANNER PAUSED")
            time.sleep(5)
            continue

        try:

            results = []

            tickers = exchange.fetch_tickers()

            btc_status = check_btc_market()

            market_universe = build_market_universe(tickers)

            print("BTC STATUS:", btc_status)
            print("UNIVERSE SIZE:", len(market_universe))

            for item in market_universe:

                try:

                    symbol = item["symbol"]

                    if btc_status == "PANIC":
                        continue

                    data = tickers[symbol]

                    last_price = data.get("last", 0)
                    bid = data.get("bid", 0)
                    ask = data.get("ask", 0)
                    volume = data.get("quoteVolume", 0)

                    if not last_price or not bid or not ask:
                        continue
                    spread_pct = ((ask - bid) / last_price) * 100

                    if spread_pct > 2:
                        continue

                    ohlcv = exchange.fetch_ohlcv(
                        symbol,
                        timeframe=config.TIMEFRAME,
                        limit=250
                    )

                    if not ohlcv:
                        continue

                    df = pd.DataFrame(
                        ohlcv,
                        columns=["time","open","high","low","close","volume"]
                    )

                    close = df["close"]
                    volume_data = df["volume"]

                    rsi = ta.momentum.RSIIndicator(close).rsi()

                    ema7 = ta.trend.EMAIndicator(close, window=7).ema_indicator()
                    ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()
                    ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()
                    latest_price = close.iloc[-1]
                    latest_open = df["open"].iloc[-1]
                    latest_rsi = rsi.iloc[-1]
                    latest_ema20 = ema20.iloc[-1]

                    latest_volume = volume_data.iloc[-1]
                    avg_volume = volume_data.tail(20).mean()
                    volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1

                    candle_pump = (
                        (latest_price - latest_open)
                        / latest_open
                    ) * 100

                    if candle_pump > 8:
                        continue

                    if latest_rsi > 80:
                        continue

                    ema_distance = (
                        (latest_price - latest_ema20)
                        / latest_ema20
                    ) * 100

                    if ema_distance > 10:
                        continue

                    multi_tf_score = get_multi_tf_score(symbol)
                    volume_score = get_volume_acceleration_score(latest_volume, avg_volume)

                    recent_high = df["high"].tail(20).max()
                    distance_to_breakout = ((recent_high - latest_price) / latest_price) * 100

                    breakout_score = 0
                    if distance_to_breakout <= 1:
                        breakout_score = 25
                    elif distance_to_breakout <= 3:
                        breakout_score = 10
                    elif distance_to_breakout > 5:
                        breakout_score = -20

                    trend_score = 0

                    if ema7.iloc[-1] > ema20.iloc[-1]:
                        trend_score += 10

                    if ema20.iloc[-1] > ema50.iloc[-1]:
                        trend_score += 10

                    if latest_price > ema20.iloc[-1]:
                        trend_score += 10
                    if ema20.iloc[-1] < ema50.iloc[-1]:
                        trend_score -= 30
                    green_count = 0

                    if df["close"].iloc[-1] > df["open"].iloc[-1]:
                        green_count += 1

                    if df["close"].iloc[-2] > df["open"].iloc[-2]:
                        green_count += 1

                    if df["close"].iloc[-3] > df["open"].iloc[-3]:
                        green_count += 1

                    if green_count < 2:
                        trend_score -= 20
                    last_high = df["high"].iloc[-1]
                    last_low = df["low"].iloc[-1]
                    last_close = df["close"].iloc[-1]

                    wick_range = ((last_high - last_low) / last_close) * 100

                    if wick_range > 8:
                        trend_score -= 40
                        print(f"{symbol} ABNORMAL WICK DETECTED: {wick_range:.2f}%")
                    body = abs(df["close"].iloc[-1] - df["open"].iloc[-1])
                    full = df["high"].iloc[-1] - df["low"].iloc[-1]

                    if full > 0:
                        body_ratio = body / full

                    if body_ratio < 0.25:
                        trend_score -= 30
                    final_score = (multi_tf_score + volume_score + breakout_score + trend_score)

                    print(f"{symbol} BreakoutDist={distance_to_breakout:.2f}% BreakoutScore={breakout_score}")
                    print(f"{symbol} TrendScore={trend_score}")
                    print(f"{symbol} GreenCandles={green_count}")
                    print(f"{symbol} VolRatio={volume_ratio:.2f} "f"VolScore={volume_score}")
                    signal = "WAIT"

                    if btc_status == "BULLISH":

                        if final_score >= 80:
                            signal = "STRONG BUY"

                        elif final_score >= 60:
                            signal = "BUY"

                        elif final_score >= 40:
                            signal = "WATCH"

                    elif btc_status == "NEUTRAL":

                        if final_score >= 80:
                            signal = "STRONG BUY"

                        elif final_score >= 40:
                            signal = "WATCH"

                    spread = ((ask - bid) / ask) * 100

                    results.append({

                        "symbol": symbol,
                        "price": last_price,
                        "volume": volume,
                        "spread": spread,
                        "signal": signal,
                        "score": round(final_score, 2),
                        "rsi": round(latest_rsi, 2)

                    })

                except Exception as e:

                    print("COIN ERROR:", str(e))

            market_data = sorted(
                results,
                key=lambda x: x["score"],
                reverse=True
            )

            print("SCANNER UPDATED:", len(market_data))

        except Exception as e:

            print("SCANNER ERROR:", str(e))

        time.sleep(config.SCANNER_INTERVAL)


def start_scanner():

    print("STARTING SCANNER THREAD")

    thread = threading.Thread(
        target=scan_market
    )

    thread.daemon = True
    thread.start()
