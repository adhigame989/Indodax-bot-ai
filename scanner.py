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

    while True:

        try:

            results = []

            tickers = exchange.fetch_tickers()

            count = 0

            for symbol in tickers:

                try:

                    # hanya IDR
                    if "/IDR" not in symbol:
                        continue

                    data = tickers[symbol]

                    last_price = data.get("last", 0)
                    bid = data.get("bid", 0)
                    ask = data.get("ask", 0)
                    volume = data.get("quoteVolume", 0)

                    if not last_price or not bid or not ask:
                        continue

                    # spread
                    spread = ((ask - bid) / ask) * 100

                    if spread > 3:
                        continue

                    # volume minimum
                    if volume < 100000000:
                        continue

                    # ambil candle
                    ohlcv = exchange.fetch_ohlcv(
                        symbol,
                        timeframe=config.TIMEFRAME,
                        limit=100
                    )

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

                    # RSI
                    rsi = ta.momentum.RSIIndicator(close).rsi()

                    # EMA
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
                    signal = "WAIT"

                    if latest_ema20 > latest_ema50:
                        score += 40

                    if latest_price > latest_ema20:
                        score += 30

                    if 45 <= latest_rsi <= 70:
                        score += 30

                    if score >= 80:
                        signal = "STRONG BUY"

                    elif score >= 60:
                        signal = "BUY"

                    elif score >= 40:
                        signal = "WATCH"

                    results.append({
                        "symbol": symbol,
                        "price": last_price,
                        "volume": volume,
                        "spread": spread,
                        "signal": signal,
                        "score": score,
                        "rsi": round(latest_rsi, 2)
                    })

                    count += 1

                    if count >= config.SCAN_LIMIT:
                        break

                except:
                    continue

            market_data = sorted(
                results,
                key=lambda x: x["score"],
                reverse=True
            )

            print("Scanner updated")

        except Exception as e:

            print("Scanner error:", e)

        # scan tiap 5 menit
        time.sleep(300)


def start_scanner():

    thread = threading.Thread(target=scan_market)

    thread.daemon = True

    thread.start()
