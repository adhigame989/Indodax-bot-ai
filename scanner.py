import ccxt
import pandas as pd
import config

exchange = ccxt.indodax({
    'enableRateLimit': True
})

def scan_market():

    results = []

    try:

        tickers = exchange.fetch_tickers()

        for symbol in tickers:

            try:

                # hanya market IDR
                if "/IDR" not in symbol:
                    continue

                data = tickers[symbol]

                last_price = data.get("last", 0)
                bid = data.get("bid", 0)
                ask = data.get("ask", 0)
                volume = data.get("quoteVolume", 0)
                percentage = data.get("percentage", 0)

                # hindari error
                if not last_price or not bid or not ask:
                    continue

                # hitung spread
                spread = ((ask - bid) / ask) * 100

                # filter spread
                if config.ENABLE_SPREAD_FILTER:
                    if spread > 3:
                        continue

                # filter volume
                if volume < 100000000:
                    continue

                results.append({
                    "symbol": symbol,
                    "price": last_price,
                    "volume": volume,
                    "change": percentage,
                    "spread": spread
                })

            except:
                continue

        # urutkan berdasarkan volume terbesar
        results = sorted(
            results,
            key=lambda x: x["volume"],
            reverse=True
        )

        return results[:config.SCAN_LIMIT]

    except Exception as e:

        return [{
            "symbol": "ERROR",
            "price": 0,
            "volume": 0,
            "change": str(e),
            "spread": 0
        }]
