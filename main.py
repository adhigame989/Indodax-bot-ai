from flask import Flask
import ccxt
import os
import config

from scanner import (
    market_data,
    start_scanner
)

app = Flask(__name__)

# START BACKGROUND SCANNER
start_scanner()

@app.route("/")
def home():

    try:

        exchange = ccxt.indodax({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'enableRateLimit': True
        })

        balance = exchange.fetch_balance()

        idr = balance['total'].get('IDR', 0)

        html = f"""
        <html>

        <head>

            <title>INDODAX AI BOT</title>

            <meta name="viewport"
            content="width=device-width, initial-scale=1">

            <style>

                body {{
                    background:#0f172a;
                    color:white;
                    font-family:Arial;
                    padding:15px;
                }}

                .card {{
                    background:#1e293b;
                    padding:15px;
                    border-radius:12px;
                    margin-bottom:15px;
                }}

                h1 {{
                    color:#38bdf8;
                }}

            </style>

        </head>

        <body>

            <h1>INDODAX AI BOT</h1>

            <div class="card">

                <h2>BOT ONLINE</h2>

                <h3>Saldo IDR</h3>

                <h1>Rp {idr:,.0f}</h1>

            </div>
        """

        for coin in market_data:

            html += f"""

            <div class="card">

                <h2>{coin['symbol']}</h2>

                <p>Signal: {coin['signal']}</p>

                <p>Score: {coin['score']}/100</p>

                <p>RSI: {coin['rsi']}</p>

                <p>Price: {coin['price']}</p>

                <p>Spread: {coin['spread']:.2f}%</p>

            </div>

            """

        html += """

        </body>
        </html>

        """

        return html

    except Exception as e:

        return f"<pre>{str(e)}</pre>"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
