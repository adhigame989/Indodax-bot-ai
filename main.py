from flask import Flask
import ccxt
import config
from scanner import scan_market

app = Flask(__name__)

@app.route("/")
def home():

    try:

        # CONNECT INDODAX
        exchange = ccxt.indodax({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'enableRateLimit': True
        })

        # GET BALANCE
        balance = exchange.fetch_balance()

        idr = balance['total'].get('IDR', 0)

        # SCAN MARKET
        markets = scan_market()

        # HTML START
        html = f"""
        <html>

        <head>

            <title>INDODAX AI BOT</title>

            <meta name="viewport" content="width=device-width, initial-scale=1">

            <style>

                body {{
                    background: #0f172a;
                    color: white;
                    font-family: Arial;
                    padding: 15px;
                    margin: 0;
                }}

                h1 {{
                    color: #38bdf8;
                    text-align: center;
                }}

                .top-card {{
                    background: #1e293b;
                    padding: 20px;
                    border-radius: 15px;
                    margin-bottom: 20px;
                }}

                .card {{
                    background: #1e293b;
                    padding: 15px;
                    border-radius: 15px;
                    margin-bottom: 15px;
                }}

                .buy {{
                    color: #22c55e;
                    font-weight: bold;
                }}

                .strong-buy {{
                    color: #00ff99;
                    font-weight: bold;
                }}

                .watch {{
                    color: #facc15;
                    font-weight: bold;
                }}

                .wait {{
                    color: #94a3b8;
                    font-weight: bold;
                }}

                .score {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #38bdf8;
                }}

                .label {{
                    color: #94a3b8;
                }}

            </style>

        </head>

        <body>

            <h1>INDODAX AI BOT</h1>

            <div class="top-card">

                <h2>BOT STATUS: ONLINE</h2>

                <h3>Saldo IDR</h3>

                <h1>Rp {idr:,.0f}</h1>

                <p>
                    TP: {config.TAKE_PROFIT}% |
                    SL: {config.STOP_LOSS}% |
                    Trailing: {config.TRAILING_GAP}%
                </p>

            </div>
        """

        # LOOP MARKET
        for coin in markets:

            signal_class = "wait"

            if coin['signal'] == "BUY":
                signal_class = "buy"

            elif coin['signal'] == "STRONG BUY":
                signal_class = "strong-buy"

            elif coin['signal'] == "WATCH":
                signal_class = "watch"

            html += f"""

            <div class="card">

                <h2>{coin['symbol']}</h2>

                <p class="{signal_class}">
                    {coin['signal']}
                </p>

                <p class="score">
                    Score: {coin['score']}/100
                </p>

                <p>
                    <span class="label">RSI:</span>
                    {coin['rsi']}
                </p>

                <p>
                    <span class="label">Price:</span>
                    {coin['price']}
                </p>

                <p>
                    <span class="label">Volume:</span>
                    {coin['volume']:,.0f}
                </p>

                <p>
                    <span class="label">Spread:</span>
                    {coin['spread']:.2f}%
                </p>

            </div>

            """

        html += """

        </body>
        </html>

        """

        return html

    except Exception as e:

        return f"""

        <html>

        <body style="background:#0f172a;color:white;font-family:Arial;padding:20px;">

            <h1>BOT ERROR</h1>

            <pre>{str(e)}</pre>

        </body>

        </html>

        """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
