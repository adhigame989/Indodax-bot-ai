from flask import Flask
import ccxt
import os
import config

from scanner import (
    market_data,
    start_scanner
)

from trader import (
    active_trade,
    start_trader
)

app = Flask(__name__)

# START BACKGROUND SYSTEM
start_scanner()
start_trader()


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

        # HTML START
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
                    margin:0;
                }}

                h1 {{
                    color:#38bdf8;
                    text-align:center;
                }}

                .card {{
                    background:#1e293b;
                    padding:15px;
                    border-radius:15px;
                    margin-bottom:15px;
                    box-shadow:0 0 10px rgba(0,0,0,0.3);
                }}

                .title {{
                    color:#38bdf8;
                    font-size:22px;
                    font-weight:bold;
                }}

                .buy {{
                    color:#22c55e;
                    font-weight:bold;
                }}

                .strong-buy {{
                    color:#00ff99;
                    font-weight:bold;
                }}

                .watch {{
                    color:#facc15;
                    font-weight:bold;
                }}

                .wait {{
                    color:#94a3b8;
                    font-weight:bold;
                }}

                .profit {{
                    color:#22c55e;
                    font-weight:bold;
                    font-size:20px;
                }}

                .loss {{
                    color:#ef4444;
                    font-weight:bold;
                    font-size:20px;
                }}

                .label {{
                    color:#94a3b8;
                }}

            </style>

        </head>

        <body>

            <h1>INDODAX AI BOT</h1>

            <div class="card">

                <div class="title">
                    BOT STATUS: ONLINE
                </div>

                <br>

                <div class="label">
                    Saldo IDR
                </div>

                <h1>
                    Rp {idr:,.0f}
                </h1>

                <p>

                    TP:
                    {config.TAKE_PROFIT}%

                    |

                    SL:
                    {config.STOP_LOSS}%

                    |

                    Trailing:
                    {config.TRAILING_GAP}%

                </p>

            </div>
        """

        # OPEN POSITION
        if active_trade:

            profit_class = "profit"

            if active_trade["profit_percent"] < 0:
                profit_class = "loss"

            html += f"""

            <div class="card">

                <div class="title">
                    OPEN POSITION
                </div>

                <br>

                <p>
                    <span class="label">Coin:</span>
                    {active_trade['symbol']}
                </p>

                <p>
                    <span class="label">Buy Price:</span>
                    {active_trade['buy_price']}
                </p>

                <p>
                    <span class="label">Current Price:</span>
                    {active_trade['current_price']}
                </p>

                <p class="{profit_class}">
                    Profit:
                    {active_trade['profit_percent']}%
                </p>

                <p>
                    <span class="label">Take Profit:</span>
                    {active_trade['tp_price']:.2f}
                </p>

                <p>
                    <span class="label">Stop Loss:</span>
                    {active_trade['sl_price']:.2f}
                </p>

            </div>

            """

        # MARKET SCANNER
        for coin in market_data:

            signal_class = "wait"

            if coin['signal'] == "BUY":
                signal_class = "buy"

            elif coin['signal'] == "STRONG BUY":
                signal_class = "strong-buy"

            elif coin['signal'] == "WATCH":
                signal_class = "watch"

            html += f"""

            <div class="card">

                <div class="title">
                    {coin['symbol']}
                </div>

                <br>

                <p class="{signal_class}">
                    {coin['signal']}
                </p>

                <p>
                    <span class="label">Score:</span>
                    {coin['score']}/100
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

        <body style="
            background:#0f172a;
            color:white;
            font-family:Arial;
            padding:20px;
        ">

            <h1>BOT ERROR</h1>

            <pre>{str(e)}</pre>

        </body>

        </html>

        """


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
