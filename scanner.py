# scanner.py

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


def check_btc_market():

    try:

        ohlcv = exchange.fetch_ohlcv(
            "BTC/IDR",
            timeframe=config.TIMEFRAME,
            limit=100
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

        print(
            "BTC RSI:",
            round(btc_rsi, 2)
        )

        print(
            "BTC CANDLE:",
            round(btc_dump, 2),
            "%"
        )

        # PANIC FILTER
        if btc_dump <= -3:

            print(
                "BTC PANIC SELL"
            )

            return False

        if btc_rsi < 35:

            print(
                "BTC RSI WEAK"
            )

            return False

        return True

    except Exception as e:

        print(
            "BTC FILTER ERROR:",
            str(e)
        )

        return True


def scan_market():

    global market_data

    print("SCANNER STARTED")

    while True:

        try:

            results = []

            tickers = exchange.fetch_tickers()

            count = 0

            btc_safe = check_btc_market()

            print(
                "BTC SAFE:",
                btc_safe
            )

            print("SCANNING MARKET...")

            for symbol in tickers:

                try:

                    if "/IDR" not in symbol:
                        continue

                    # skip BTC sendiri
                    if symbol == "BTC/IDR":
                        continue

                    print("CHECK:", symbol)

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

                    if (
                        volume <
                        config.MIN_VOLUME
                    ):
                        continue

                    print(
                        "FETCHING:",
                        symbol
                    )

                    ohlcv = exchange.fetch_ohlcv(
                        symbol,
                        timeframe=config.TIMEFRAME,
                        limit=100
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

                    ema50 = ta.trend.EMAIndicator(
                        close,
                        window=50
                    ).ema_indicator()

                    latest_rsi = rsi.iloc[-1]

                    latest_ema20 = ema20.iloc[-1]

                    latest_ema50 = ema50.iloc[-1]

                    latest_price = close.iloc[-1]

                    latest_open = df[
                        'open'
                    ].iloc[-1]

                    latest_volume = volume_data.iloc[-1]

                    avg_volume = (
                        volume_data.tail(20).mean()
                    )

                    score = 0

                    signal = "WAIT"

                    # =========================
                    # BTC PANIC FILTER
                    # =========================

                    if not btc_safe:

                        print(
                            "SKIP BTC PANIC:",
                            symbol
                        )

                        continue

                    # =========================
                    # ANTI FOMO FILTER
                    # =========================

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

                    # =========================
                    # SCORING
                    # =========================

                    if latest_ema20 > latest_ema50:
                        score += 40

                    if latest_price > latest_ema20:
                        score += 30

                    if 40 <= latest_rsi <= 75:
                        score += 30

                    if latest_volume > avg_volume:
                        score += 10

                    if latest_price > latest_open:
                        score += 10

                    # market sehat bonus
                    if btc_safe:
                        score += 10

                    if score >= 70:

                        signal = "STRONG BUY"

                    elif score >= 50:

                        signal = "BUY"

                    elif score >= 30:

                        signal = "WATCH"

                    print(
                        "COIN PASSED:",
                        symbol,
                        signal,
                        score
                    )

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
                        score,

                        "rsi":
                        round(
                            latest_rsi,
                            2
                        )

                    })

                    count += 1

                    if (
                        count >=
                        config.SCAN_LIMIT
                    ):
                        break

                except Exception as e:

                    print(
                        "COIN ERROR:",
                        symbol,
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
                len(market_data),
                "COINS"
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
