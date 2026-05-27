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


def scan_market():

    global market_data

    print("SCANNER STARTED")

    while True:

        try:

            results = []

            tickers = exchange.fetch_tickers()

            count = 0

            print("SCANNING MARKET...")

            for symbol in tickers:

                try:

                    if "/IDR" not in symbol:
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

                    print("FETCHING:", symbol)

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

                    # =================================
                    # ANTI FOMO FILTER
                    # =================================

                    candle_pump = (
                        (
                            latest_price -
                            latest_open
                        )
                        /
                        latest_open
                    ) * 100

                    # skip candle pump
                    if candle_pump > 8:

                        print(
                            "SKIP PUMP:",
                            symbol
                        )

                        continue

                    # skip RSI panas
                    if latest_rsi > 80:

                        print(
                            "SKIP RSI HOT:",
                            symbol
                        )

                        continue

                    # skip jauh dari EMA20
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

                    # skip volume abnormal
                    if latest_volume > (
                        avg_volume * 5
                    ):

                        print(
                            "SKIP VOLUME SPIKE:",
                            symbol
                        )

                        continue

                    # =================================
                    # SCORING
                    # =================================

                    if latest_ema20 > latest_ema50:
                        score += 40

                    if latest_price > latest_ema20:
                        score += 30

                    if 40 <= latest_rsi <= 75:
                        score += 30

                    # volume bagus
                    if latest_volume > avg_volume:
                        score += 10

                    # bullish candle
                    if latest_price > latest_open:
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
