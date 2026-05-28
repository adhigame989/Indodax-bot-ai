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
                    margin:0;
                    padding:0;
                    box-sizing:border-box;
                }}

                body {{

                    background:
                    linear-gradient(
                        180deg,
                        #020617,
                        #020b1d
                    );

                    color:white;

                    font-family:
                    Arial,
                    sans-serif;

                    padding:18px;

                }}

                .topbar {{

                    background:
                    linear-gradient(
                        135deg,
                        #0f172a,
                        #111827
                    );

                    border:
                    1px solid #1e293b;

                    border-radius:24px;

                    padding:22px;

                    margin-bottom:20px;

                    box-shadow:
                    0 0 30px rgba(
                        14,
                        165,
                        233,
                        0.15
                    );

                }}

                .logo {{

                    font-size:34px;

                    font-weight:bold;

                    color:#38bdf8;

                    margin-bottom:8px;

                }}

                .subtitle {{

                    color:#94a3b8;

                    font-size:14px;

                }}

                .stats-grid {{

                    display:grid;

                    grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(160px,1fr)
                    );

                    gap:14px;

                    margin-bottom:22px;

                }}

                .card {{

                    background:
                    linear-gradient(
                        145deg,
                        #0f172a,
                        #111827
                    );

                    border:
                    1px solid #1e293b;

                    border-radius:22px;

                    padding:18px;

                    box-shadow:
                    0 0 20px rgba(
                        0,
                        0,
                        0,
                        0.25
                    );

                }}

                .card-title {{

                    color:#94a3b8;

                    font-size:13px;

                    margin-bottom:10px;

                    letter-spacing:1px;

                }}

                .card-value {{

                    font-size:30px;

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

                .blue {{
                    color:#38bdf8;
                }}

                .section-title {{

                    font-size:22px;

                    font-weight:bold;

                    color:#38bdf8;

                    margin-top:25px;

                    margin-bottom:14px;

                }}

                .trade-box {{

                    background:
                    linear-gradient(
                        145deg,
                        #111827,
                        #0f172a
                    );

                    border:
                    1px solid #1f2937;

                    border-radius:24px;

                    padding:22px;

                    margin-bottom:20px;

                    box-shadow:
                    0 0 25px rgba(
                        0,
                        0,
                        0,
                        0.35
                    );

                }}

                .trade-symbol {{

                    font-size:30px;

                    font-weight:bold;

                    margin-bottom:16px;

                    color:#38bdf8;

                }}

                .row {{

                    display:flex;

                    justify-content:
                    space-between;

                    align-items:center;

                    margin-bottom:12px;

                    color:#cbd5e1;

                    font-size:15px;

                }}

                .profit-big {{

                    font-size:34px;

                    font-weight:bold;

                    margin-top:12px;

                }}

                .scanner-grid {{

                    display:grid;

                    grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(240px,1fr)
                    );

                    gap:15px;

                }}

                .coin-card {{

                    background:
                    linear-gradient(
                        145deg,
                        #0f172a,
                        #111827
                    );

                    border:
                    1px solid #1e293b;

                    border-radius:22px;

                    padding:18px;

                    box-shadow:
                    0 0 18px rgba(
                        0,
                        0,
                        0,
                        0.25
                    );

                }}

                .coin-name {{

                    font-size:22px;

                    font-weight:bold;

                    margin-bottom:14px;

                    color:#38bdf8;

                }}

                .signal {{

                    display:inline-block;

                    padding:
                    8px 14px;

                    border-radius:999px;

                    font-size:13px;

                    font-weight:bold;

                    margin-bottom:15px;

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

                .history-card {{

                    background:
                    linear-gradient(
                        145deg,
                        #111827,
                        #0f172a
                    );

                    border:
                    1px solid #1f2937;

                    border-radius:20px;

                    padding:16px;

                    margin-bottom:12px;

                }}

                .status-bar {{

                    display:flex;

                    justify-content:
                    space-between;

                    align-items:center;

                    background:
                    #0f172a;

                    border:
                    1px solid #1e293b;

                    border-radius:18px;

                    padding:14px 18px;

                    margin-bottom:20px;

                }}

                .status-dot {{

                    width:12px;

                    height:12px;

                    border-radius:50%;

                    background:#22c55e;

                    box-shadow:
                    0 0 12px #22c55e;

                }}

                .footer {{

                    text-align:center;

                    color:#64748b;

                    font-size:12px;

                    margin-top:30px;

                    padding-bottom:30px;

                }}

                .bottom-nav {{

                    position:fixed;

                    bottom:0;

                    left:0;

                    width:100%;

                    background:#0f172a;

                    border-top:
                    1px solid #1e293b;

                    display:flex;

                    justify-content:
                    space-around;

                    padding:12px 0;

                    z-index:999;

                }}

                .nav-item {{

                    text-align:center;

                    color:#94a3b8;

                    font-size:12px;

                }}

                .nav-icon {{

                    font-size:20px;

                    margin-bottom:4px;

                }}

            </style>

        </head>

        <body>

            <div class="topbar">

                <div class="logo">
                    INDODAX AI BOT
                </div>

                <div class="subtitle">
                    AI Trading Dashboard
                </div>

            </div>

            <div class="status-bar">

                <div>
                    BOT STATUS
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                    gap:10px;
                ">

                    <div class="status-dot"></div>

                    <div class="green">
                        RUNNING
                    </div>

                </div>

            </div>

            <div class="stats-grid">

                <div class="card">

                    <div class="card-title">
                        WALLET
                    </div>

                    <div class="card-value green">
                        Rp {idr:,.0f}
                    </div>

                </div>

                <div class="card">

                    <div class="card-title">
                        TOTAL TRADES
                    </div>

                    <div class="card-value blue">
                        {stats['total_trades']}
                    </div>

                </div>

                <div class="card">

                    <div class="card-title">
                        WINRATE
                    </div>

                    <div class="card-value green">
                        {stats['winrate']}%
                    </div>

                </div>

                <div class="card">

                    <div class="card-title">
                        TOTAL PROFIT
                    </div>

                    <div class="card-value yellow">
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

            <div class="trade-box">

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
                    <span class="green">
                    {trader.active_trade['tp_price']}
                    </span>
                </div>

                <div class="row">
                    <span>Stop Loss</span>
                    <span class="red">
                    {trader.active_trade['sl_price']}
                    </span>
                </div>

                <div class="profit-big {profit_class}">
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

            <div class="history-card">

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
                INDODAX AI BOT • Railway Mobile App
            </div>

            <div class="bottom-nav">

                <div class="nav-item">
                    <div class="nav-icon">🏠</div>
                    Home
                </div>

                <div class="nav-item">
                    <div class="nav-icon">📈</div>
                    Scanner
                </div>

                <div class="nav-item">
                    <div class="nav-icon">🤖</div>
                    Bot
                </div>

                <div class="nav-item">
                    <div class="nav-icon">📜</div>
                    History
                </div>

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
