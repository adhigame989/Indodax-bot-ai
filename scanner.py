import ccxt
import threading
import time
import pandas as pd
import ta
import config

exchange = ccxt.indodax({
    'enableRateLimit': True
})

market_data = []


def get_multi_tf_score(symbol):

    try:

        timeframes = [
            "15m",
            "1h"
        ]

        total_score = 0

        for tf in timeframes:

            ohlcv = exchange.fetch_ohlcv(
                symbol,
                timeframe=tf,
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

            score = 0

            if latest_ema20 > latest_ema50:
                score += 40

            if latest_price > latest_ema20:
                score += 30

            if 40 <= latest_rsi <= 75:
                score += 30

            total_score += score

        final_score = total_score / 2

        return round(final_score, 2)

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
            timeframe=config.TIMEFRAME,
            limit=60
        )

        if not ohlcv:
            return True

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

        latest_price = close.iloc[-1]

        latest_open = df['open'].iloc[-1]

        btc_rsi = ta.momentum.RSIIndicator(
            close
        ).rsi().iloc[-1]

        btc_dump = (
            (
                latest_price -
                latest_open
            )
            /
            latest_open
        ) * 100

        if btc_dump <= -3:
            return False

        if btc_rsi < 35:
            return False

        return True

    except Exception as e:

        print(
            "BTC FILTER ERROR:",
            str(e)
        )

        return True


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

        try:

            results = []

            tickers = exchange.fetch_tickers()

            btc_safe = check_btc_market()

            print(
                "BTC SAFE:",
                btc_safe
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

                    if not btc_safe:

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

                    if multi_tf_score >= 75:
                        signal = "STRONG BUY"

                    elif multi_tf_score >= 55:
                        signal = "BUY"

                    elif multi_tf_score >= 35:
                        signal = "WATCH"

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
