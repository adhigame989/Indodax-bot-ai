from flask import Flask
import ccxt
import os
import config
import trader

from scanner import (
    market_data,
    start_scanner
)

from trader import (
    start_trader
)

from history import (
    get_stats
)

app = Flask(__name__)

start_scanner()
start_trader()


@app.route("/")
def home():

    try:

        exchange = ccxt.indodax({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'enableRateLimit': True
        })

        balance = exchange.fetch_balance()

        idr = balance['total'].get(
            'IDR',
            0
        )

        stats = get_stats()

        html = f"""

        <html>

        <head>

            <title>
            INDODAX AI BOT
            </title>

            <meta
            name="viewport"
            content="width=device-width,
            initial-scale=1">

            <link
            rel="manifest"
            href="/static/manifest.json">

            <meta
            name="theme-color"
            content="#0ea5e9">

            <meta
            name="mobile-web-app-capable"
            content="yes">

            <meta
            name="apple-mobile-web-app-capable"
            content="yes">

            <meta
            name="apple-mobile-web-app-status-bar-style"
            content="black-translucent">

            <style>

                * {{
                    box-sizing:border-box;
                }}

                body {{

                    margin:0;
                    padding:20px;
                    background:#020617;
                    color:white;
                    font-family:Arial;

                }}

                .header {{

                    background:linear-gradient(
                        135deg,
                        #0f172a,
                        #1e293b
                    );

                    padding:25px;
                    border-radius:25px;
                    margin-bottom:20px;
                    border:1px solid #334155;
                    box-shadow:
                    0 0 20px rgba(0,0,0,0.4);

                }}

                .title {{

                    font-size:34px;
                    font-weight:bold;
                    color:#38bdf8;

                }}

                .subtitle {{

                    color:#94a3b8;
                    margin-top:8px;
                    font-size:15px;

                }}

                .grid {{

                    display:grid;
                    grid-template-columns:
                    repeat(auto-fit,minmax(220px,1fr));
                    gap:15px;
                    margin-bottom:20px;

                }}

                .card {{

                    background:#0f172a;
                    border:1px solid #1e293b;
                    border-radius:22px;
                    padding:18px;
                    box-shadow:
                    0 0 15px rgba(0,0,0,0.25);

                }}

                .card-title {{

                    color:#38bdf8;
                    font-size:16px;
                    margin-bottom:10px;
                    font-weight:bold;
                    letter-spacing:1px;

                }}

                .big-number {{

                    font-size:28px;
                    font-weight:bold;

                }}

                .green {{
                    color:#22c55e;
                }}

                .red {{
                    color:#ef4444;
                }}

                .yellow {{
                    color:#facc15;
                }}

                .gray {{
                    color:#94a3b8;
                }}

                .section-title {{

                    font-size:22px;
                    font-weight:bold;
                    margin-top:25px;
                    margin-bottom:15px;
                    color:#38bdf8;

                }}

                .trade-card {{

                    background:#111827;
                    border-radius:20px;
                    padding:18px;
                    margin-bottom:15px;
                    border:1px solid #1f2937;

                }}

                .trade-symbol {{

                    font-size:24px;
                    font-weight:bold;
                    margin-bottom:12px;

                }}

                .trade-profit {{

                    font-size:24px;
                    font-weight:bold;
                    margin-top:10px;

                }}

                .scanner-grid {{

                    display:grid;
                    grid-template-columns:
                    repeat(auto-fit,minmax(260px,1fr));
                    gap:15px;

                }}

                .coin-card {{

                    background:#0f172a;
                    border-radius:20px;
                    padding:18px;
                    border:1px solid #1e293b;

                }}

                .coin-name {{

                    font-size:22px;
                    font-weight:bold;
                    margin-bottom:12px;

                }}

                .signal {{

                    display:inline-block;
                    padding:8px 14px;
                    border-radius:999px;
                    font-weight:bold;
                    margin-bottom:15px;
                    font-size:14px;

                }}

                .buy {{

                    background:#14532d;
                    color:#4ade80;

                }}

                .strong-buy {{

                    background:#064e3b;
                    color:#34d399;

                }}

                .watch {{

                    background:#713f12;
                    color:#facc15;

                }}

                .wait {{

                    background:#1e293b;
                    color:#94a3b8;

                }}

                .row {{

                    display:flex;
                    justify-content:space-between;
                    margin-bottom:8px;
                    color:#cbd5e1;

                }}

                .history-item {{

                    background:#111827;
                    border-radius:16px;
                    padding:14px;
                    margin-bottom:10px;
                    border:1px solid #1f2937;

                }}

                .footer {{

                    text-align:center;
                    color:#64748b;
                    margin-top:30px;
                    font-size:13px;

                }}

            </style>

        </head>

        <body>

            <div class="header">

                <div class="title">
                    INDODAX AI BOT
                </div>

                <div class="subtitle">
                    Railway Live Trading Dashboard
                </div>

            </div>

            <div class="grid">

                <div class="card">
                    <div class="card-title">
                        WALLET
                    </div>
                    <div class="big-number green">
                        Rp {idr:,.0f}
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">
                        TOTAL TRADES
                    </div>
                    <div class="big-number">
                        {stats['total_trades']}
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">
                        WINRATE
                    </div>
                    <div class="big-number green">
                        {stats['winrate']}%
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">
                        TOTAL PROFIT
                    </div>
                    <div class="big-number yellow">
                        {stats['total_profit']}%
                    </div>
                </div>

            </div>

        """

        if trader.active_trade:

            profit_class = "green"

            if (
                trader.active_trade[
                    "profit_percent"
                ] < 0
            ):

                profit_class = "red"

            html += f"""

            <div class="section-title">
                OPEN POSITION
            </div>

            <div class="trade-card">

                <div class="trade-symbol">
                    {trader.active_trade['symbol']}
                </div>

                <div class="row">
                    <span>Buy Price</span>
                    <span>
                    {trader.active_trade['buy_price']}
                    </span>
                </div>

                <div class="row">
                    <span>Current Price</span>
                    <span>
                    {trader.active_trade['current_price']}
                    </span>
                </div>

                <div class="row">
                    <span>Take Profit</span>
                    <span>
                    {trader.active_trade['tp_price']}
                    </span>
                </div>

                <div class="row">
                    <span>Stop Loss</span>
                    <span>
                    {trader.active_trade['sl_price']}
                    </span>
                </div>

                <div class="trade-profit {profit_class}">
                    {trader.active_trade['profit_percent']}%
                </div>

            </div>

            """

        html += """

        <div class="section-title">
            MARKET SCANNER
        </div>

        <div class="scanner-grid">

        """

        for coin in market_data:

            signal_class = "wait"

            if coin['signal'] == "BUY":
                signal_class = "buy"

            elif coin['signal'] == "STRONG BUY":
                signal_class = "strong-buy"

            elif coin['signal'] == "WATCH":
                signal_class = "watch"

            html += f"""

            <div class="coin-card">

                <div class="coin-name">
                    {coin['symbol']}
                </div>

                <div class="signal {signal_class}">
                    {coin['signal']}
                </div>

                <div class="row">
                    <span>Score</span>
                    <span>{coin['score']}</span>
                </div>

                <div class="row">
                    <span>RSI</span>
                    <span>{coin['rsi']}</span>
                </div>

                <div class="row">
                    <span>Price</span>
                    <span>{coin['price']}</span>
                </div>

                <div class="row">
                    <span>Volume</span>
                    <span>{coin['volume']:,.0f}</span>
                </div>

                <div class="row">
                    <span>Spread</span>
                    <span>{coin['spread']:.2f}%</span>
                </div>

            </div>

            """

        html += """

        </div>

        <div class="section-title">
            TRADE HISTORY
        </div>

        """

        for trade_data in stats['history'][:10]:

            color = "green"

            if trade_data['profit_percent'] < 0:
                color = "red"

            html += f"""

            <div class="history-item">

                <div class="row">
                    <span>{trade_data['symbol']}</span>
                    <span class="{color}">
                    {trade_data['profit_percent']}%
                    </span>
                </div>

                <div class="row">
                    <span>{trade_data['side']}</span>
                    <span>{trade_data['time']}</span>
                </div>

            </div>

            """

        html += """

            <div class="footer">
                INDODAX AI BOT • Railway Live Server
            </div>

            <script>

            if ('serviceWorker' in navigator) {

                navigator.serviceWorker.register(
                    '/static/sw.js'
                )

            }

            </script>

        </body>
        </html>

        """

        return html

    except Exception as e:

        return f"""

        <html>

        <body style="
            background:#020617;
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

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
