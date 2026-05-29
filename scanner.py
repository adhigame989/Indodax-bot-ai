import ccxt
import threading
import time
import pandas as pd
import ta
import config

BOT_RUNNING = False

exchange = ccxt.indodax({
    'enableRateLimit': True
})

market_data = []

recent_logs = []


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

        if not tf_15m:
            return 0

        if not tf_1h:
            return 0

        if not tf_4h:
            return 0

        df_15m = pd.DataFrame(
            tf_15m,
            columns=[
                'time',
                'open',
                'high',
                'low',
                'close',
                'volume'
            ]
        )

        df_1h = pd.DataFrame(
            tf_1h,
            columns=[
                'time',
                'open',
                'high',
                'low',
                'close',
                'volume'
            ]
        )

        df_4h = pd.DataFrame(
            tf_4h,
            columns=[
                'time',
                'open',
                'high',
                'low',
                'close',
                'volume'
            ]
        )

        close_15m = df_15m['close']
        close_1h = df_1h['close']
        close_4h = df_4h['close']

        rsi_15m = ta.momentum.RSIIndicator(
            close_15m
        ).rsi()

        ema20_15m = ta.trend.EMAIndicator(
            close_15m,
            window=20
        ).ema_indicator()

        ema50_15m = ta.trend.EMAIndicator(
            close_15m,
            window=50
        ).ema_indicator()

        latest_price_15m = close_15m.iloc[-1]

        latest_rsi_15m = rsi_15m.iloc[-1]

        latest_ema20_15m = ema20_15m.iloc[-1]

        latest_ema50_15m = ema50_15m.iloc[-1]

        if latest_ema20_15m > latest_ema50_15m:
            score_15m += 40

        if latest_price_15m > latest_ema20_15m:
            score_15m += 30

        if 40 <= latest_rsi_15m <= 75:
            score_15m += 30

        rsi_1h = ta.momentum.RSIIndicator(
            close_1h
        ).rsi()

        ema20_1h = ta.trend.EMAIndicator(
            close_1h,
            window=20
        ).ema_indicator()

        ema50_1h = ta.trend.EMAIndicator(
            close_1h,
            window=50
        ).ema_indicator()

        latest_price_1h = close_1h.iloc[-1]

        latest_rsi_1h = rsi_1h.iloc[-1]

        latest_ema20_1h = ema20_1h.iloc[-1]

        latest_ema50_1h = ema50_1h.iloc[-1]

        if latest_ema20_1h > latest_ema50_1h:
            score_1h += 40

        if latest_price_1h > latest_ema20_1h:
            score_1h += 30

        if 40 <= latest_rsi_1h <= 75:
            score_1h += 30

        ema20_4h = ta.trend.EMAIndicator(
            close_4h,
            window=20
        ).ema_indicator()

        ema50_4h = ta.trend.EMAIndicator(
            close_4h,
            window=50
        ).ema_indicator()

        latest_ema20_4h = ema20_4h.iloc[-1]

        latest_ema50_4h = ema50_4h.iloc[-1]

        if latest_ema20_4h > latest_ema50_4h:
            score_4h = 20

        final_score = (
            score_15m +
            score_1h +
            score_4h
        ) / 2.2

        return round(
            final_score,
            2
        )

    except Exception as e:

        print(
            "MULTI TF ERROR:",
            symbol,
            str(e)
        )

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
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )

        close = df["close"]

        rsi = ta.momentum.RSIIndicator(
            close
        ).rsi()

        ema20 = ta.trend.EMAIndicator(
            close,
            window=20
        ).ema_indicator()

        ema50 = ta.trend.EMAIndicator(
            close,
            window=50
        ).ema_indicator()

        latest_rsi = rsi.iloc[-1]

        latest_ema20 = ema20.iloc[-1]

        latest_ema50 = ema50.iloc[-1]

        latest_price = close.iloc[-1]

        latest_open = df["open"].iloc[-1]

        btc_change = (
            (
                latest_price -
                latest_open
            )
            /
            latest_open
        ) * 100

        if (
            btc_change <= -3
            or
            latest_rsi < 35
        ):
            return "PANIC"

        if (
            latest_rsi > 55
            and
            latest_ema20 > latest_ema50
        ):
            return "BULLISH"

        return "NEUTRAL"

    except Exception as e:

        print(
            "BTC FILTER ERROR:",
            str(e)
        )

        return "NEUTRAL"


def build_market_universe(tickers):

    try:

        candidates = []

        for symbol in tickers:

            try:

                if "/IDR" not in symbol:
                    continue

                if symbol == "BTC/IDR":
                    continue

                data = tickers[symbol]

                volume = data.get(
                    "quoteVolume",
                    0
                )

                bid = data.get(
                    "bid",
                    0
                )

                ask = data.get(
                    "ask",
                    0
                )

                last = data.get(
                    "last",
                    0
                )

                percentage = data.get(
                    "percentage",
                    0
                )

                if not volume:
                    continue

                if not bid:
                    continue

                if not ask:
                    continue

                if not last:
                    continue

                if (
                    volume <
                    config.MIN_VOLUME
                ):
                    continue

                spread = (
                    (ask - bid)
                    / ask
                ) * 100

                if (
                    config.ENABLE_SPREAD_FILTER
                    and
                    spread > config.MAX_SPREAD
                ):
                    continue

                score = 0

                if percentage:
                    score += abs(
                        percentage
                    ) * 2

                relative_volume = (
                    volume /
                    config.MIN_VOLUME
                )

                score += relative_volume

                if spread < 0.5:
                    score += 15

                if volume > (
                    config.MIN_VOLUME * 5
                ):
                    score += 20

                candidates.append({

                    "symbol":
                    symbol,

                    "score":
                    score,

                    "volume":
                    volume

                })

            except Exception as e:

                print(
                    "UNIVERSE ERROR:",
                    symbol,
                    str(e)
                )

                continue

        candidates = sorted(
            candidates,
            key=lambda x: x["score"],
            reverse=True
        )

        return candidates[
            :config.SCAN_LIMIT
        ]

    except Exception as e:

        print(
            "BUILD UNIVERSE ERROR:",
            str(e)
        )

        return []


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
            print(
                "BTC STATUS:",
                btc_status
            )

            market_universe = (
                build_market_universe(
                    tickers
                )
            )

            print(
                "UNIVERSE SIZE:",
                len(market_universe)
            )

            for item in market_universe:

                try:

                    symbol = item["symbol"]

                    data = tickers[symbol]

                    last_price = data.get(
                        "last",
                        0
                    )

                    bid = data.get(
                        "bid",
                        0
                    )

                    ask = data.get(
                        "ask",
                        0
                    )

                    volume = data.get(
                        "quoteVolume",
                        0
                    )

                    if not last_price:
                        continue

                    if not bid:
                        continue

                    if not ask:
                        continue

                    if btc_status == "PANIC":

                        print(
                            "BTC PANIC:",
                            symbol
                        )

                        continue

                    ohlcv = exchange.fetch_ohlcv(
                        symbol,
                        timeframe=config.TIMEFRAME,
                        limit=60
                    )

                    if not ohlcv:
                        continue

                    df = pd.DataFrame(
                        ohlcv,
                        columns=[
                            'time',
                            'open',
                            'high',
                            'low',
                            'close',
                            'volume'
                        ]
                    )

                    close = df['close']

                    volume_data = df['volume']

                    rsi = ta.momentum.RSIIndicator(
                        close
                    ).rsi()

                    ema20 = ta.trend.EMAIndicator(
                        close,
                        window=20
                    ).ema_indicator()

                    latest_rsi = rsi.iloc[-1]

                    latest_ema20 = ema20.iloc[-1]

                    latest_price = close.iloc[-1]

                    latest_open = df[
                        'open'
                    ].iloc[-1]

                    latest_volume = volume_data.iloc[-1]

                    avg_volume = (
                        volume_data.tail(20).mean()
                    )

                    candle_pump = (
                        (
                            latest_price -
                            latest_open
                        )
                        /
                        latest_open
                    ) * 100

                    if candle_pump > 8:

                        print(
                            "SKIP PUMP:",
                            symbol
                        )

                        continue

                    if latest_rsi > 80:

                        print(
                            "SKIP RSI HOT:",
                            symbol
                        )

                        continue

                    ema_distance = (
                        (
                            latest_price -
                            latest_ema20
                        )
                        /
                        latest_ema20
                    ) * 100

                    if ema_distance > 10:

                        print(
                            "SKIP EMA FAR:",
                            symbol
                        )

                        continue

                    if latest_volume > (
                        avg_volume * 5
                    ):

                        print(
                            "SKIP VOLUME SPIKE:",
                            symbol
                        )

                        continue

                    multi_tf_score = (
                        get_multi_tf_score(
                            symbol
                        )
                    )

                    signal = "WAIT"

                    signal = "WAIT"

                    if btc_status == "BULLISH":

                        if multi_tf_score >= 75:
                            signal = "STRONG BUY"

                        elif multi_tf_score >= 55:
                            signal = "BUY"

                        elif multi_tf_score >= 35:
                            signal = "WATCH"

                    elif btc_status == "NEUTRAL":

                        if multi_tf_score >= 75:
                            signal = "STRONG BUY"

                        elif multi_tf_score >= 35:
                            signal = "WATCH"

                    else:

                        signal = "WAIT"

                    spread = (
                        (ask - bid)
                        / ask
                    ) * 100

                    results.append({

                        "symbol":
                        symbol,

                        "price":
                        last_price,

                        "volume":
                        volume,

                        "spread":
                        spread,

                        "signal":
                        signal,

                        "score":
                        round(
                            multi_tf_score,
                            2
                        ),

                        "rsi":
                        round(
                            latest_rsi,
                            2
                        )

                    })

                    print(
                        "SCANNED:",
                        symbol,
                        signal,
                        multi_tf_score
                    )

                except Exception as e:

                    print(
                        "COIN ERROR:",
                        str(e)
                    )
                    recent_logs.insert(
                        0,
                        f"{symbol} | {signal} | {round(multi_tf_score, 2)}"
                    )

                    recent_logs[:] = recent_logs[:20]

                    continue

            market_data = sorted(
                results,
                key=lambda x: x["score"],
                reverse=True
            )

            print(
                "SCANNER UPDATED:",
                len(market_data)
            )

        except Exception as e:

            print(
                "SCANNER ERROR:",
                str(e)
            )

        time.sleep(
            config.SCANNER_INTERVAL
        )


def start_scanner():

    print(
        "STARTING SCANNER THREAD"
    )

    thread = threading.Thread(
        target=scan_market
    )

    thread.daemon = True

    thread.start()
