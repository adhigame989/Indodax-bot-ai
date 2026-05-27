# main.py

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
                    box-shadow:
                    0 0 10px
                    rgba(0,0,0,0.3);

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

                hr {{

                    border:none;
                    border-top:
                    1px solid #334155;

                }}

            </style>

        </head>

        <body>

            <h1>
            INDODAX AI BOT
            </h1>

            <div class="card">

                <div class="title">
                    BOT STATUS
                </div>

                <br>

                <p>
                    ONLINE
                </p>

                <p>
                    IDR:
                    Rp {idr:,.0f}
                </p>

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

            <div class="card">

                <div class="title">
                    BOT STATS
                </div>

                <br>

                <p>
                    Total Trades:
                    {stats['total_trades']}
                </p>

                <p>
                    Win:
                    {stats['win']}
                </p>

                <p>
                    Loss:
                    {stats['loss']}
                </p>

                <p>
                    Winrate:
                    {stats['winrate']}%
                </p>

                <p>
                    Total Profit:
                    {stats['total_profit']}%
                </p>

            </div>

        """

        if trader.active_trade:

            profit_class = "profit"

            if (
                trader.active_trade[
                    "profit_percent"
                ] < 0
            ):

                profit_class = "loss"

            html += f"""

            <div class="card">

                <div class="title">
                    OPEN POSITION
                </div>

                <br>

                <p>

                    Coin:

                    {trader.active_trade['symbol']}

                </p>

                <p>

                    Buy Price:

                    {
                        trader.active_trade[
                            'buy_price'
                        ]
                    }

                </p>

                <p>

                    Current Price:

                    {
                        trader.active_trade[
                            'current_price'
                        ]
                    }

                </p>

                <p class="{profit_class}">

                    Profit:

                    {
                        trader.active_trade[
                            'profit_percent'
                        ]
                    }%

                </p>

                <p>

                    TP:

                    {
                        trader.active_trade[
                            'tp_price'
                        ]
                    }

                </p>

                <p>

                    SL:

                    {
                        trader.active_trade[
                            'sl_price'
                        ]
                    }

                </p>

            </div>

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

            <div class="card">

                <div class="title">

                    {coin['symbol']}

                </div>

                <br>

                <p class="{signal_class}">

                    {coin['signal']}

                </p>

                <p>

                    Score:
                    {coin['score']}/100

                </p>

                <p>

                    RSI:
                    {coin['rsi']}

                </p>

                <p>

                    Price:
                    {coin['price']}

                </p>

                <p>

                    Volume:
                    {coin['volume']:,.0f}

                </p>

                <p>

                    Spread:
                    {coin['spread']:.2f}%

                </p>

            </div>

            """

        html += """

        <div class="card">

            <div class="title">
                TRADE HISTORY
            </div>

            <br>

        """

        for trade_data in stats["history"][:10]:

            html += f"""

            <p>

                {trade_data['time']}

                <br><br>

                {trade_data['symbol']}

                |

                {trade_data['side']}

                |

                {trade_data['profit_percent']}%

            </p>

            <hr>

            """

        html += """

        </div>

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
