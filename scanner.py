import ccxt
import pandas as pd
import ta
import config

exchange = ccxt.indodax({
    'enableRateLimit': True
})

def get_ohlcv(symbol):

    try:

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

        return df

    except:

        return None


def calculate_signal(df):

    try:

        close = df['close']

        # RSI
        rsi = ta.momentum.RSIIndicator(close).rsi()

        # EMA
        ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()

        latest_rsi = rsi.iloc[-1]
        latest_ema20 = ema20.iloc[-1]
        latest_ema50 = ema50.iloc[-1]
        latest_price = close.iloc[-1]

        score = 0
        signal = "WAIT"

        # Trend bullish
        if latest_ema20 > latest_ema50:
            score += 40

        # Price di atas EMA20
        if latest_price > latest_ema20:
            score += 30

        # RSI sehat
        if 45 <= latest_rsi <= 70:
            score += 30

        # Tentukan signal
        if score >= 80:
            signal = "STRONG BUY"

        elif score >= 60:
            signal = "BUY"

        elif score >= 40:
            signal = "WATCH"

        return {
            "score": score,
            "signal": signal,
            "rsi": round(latest_rsi, 2)
        }

    except:

        return {
            "score": 0,
            "signal": "ERROR",
            "rsi": 0
        }


def scan_market():

    results = []

    try:

        tickers = exchange.fetch_tickers()

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

                if config.ENABLE_SPREAD_FILTER:
                    if spread > 3:
                        continue

                # volume minimum
                if volume < 100000000:
                    continue

                # ambil candle
                df = get_ohlcv(symbol)

                if df is None:
                    continue

                analysis = calculate_signal(df)

                results.append({
                    "symbol": symbol,
                    "price": last_price,
                    "volume": volume,
                    "spread": spread,
                    "signal": analysis["signal"],
                    "score": analysis["score"],
                    "rsi": analysis["rsi"]
                })

            except:
                continue

        # sort score tertinggi
        results = sorted(
            results,
            key=lambda x: x["score"],
            reverse=True
        )

        return results[:config.SCAN_LIMIT]

    except Exception as e:

        return [{
            "symbol": "ERROR",
            "price": 0,
            "volume": 0,
            "spread": 0,
            "signal": str(e),
            "score": 0,
            "rsi": 0
        }]
