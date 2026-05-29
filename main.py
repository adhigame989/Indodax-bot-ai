from flask import Flask, redirect
import ccxt
import os
import config
import trader
import scanner

from scanner import start_scanner
from trader import start_trader
from history import get_stats

app = Flask(__name__)

BOT_RUNNING = False

start_scanner()
start_trader()


def pwa():
    return """
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#0ea5e9">
    """


def style():
    return """
    <style>
    body{
        background:#020617;
        color:white;
        font-family:Arial,sans-serif;
        margin:0;
        padding:15px;
        padding-bottom:90px;
    }

    .topbar{
        background:#0f172a;
        padding:20px;
        border-radius:20px;
        border:1px solid #1e293b;
        margin-bottom:15px;
    }

    .logo{
        font-size:28px;
        font-weight:bold;
        color:#38bdf8;
    }

    .subtitle{
        color:#94a3b8;
        font-size:13px;
    }

    .grid{
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
        gap:10px;
    }

    .card,.trade-box,.table-box{
        background:#0f172a;
        border:1px solid #1e293b;
        border-radius:18px;
        padding:15px;
        margin-bottom:12px;
    }

    .title{color:#94a3b8;font-size:12px;}
    .value{font-size:24px;font-weight:bold;margin-top:5px;}

    .green{color:#22c55e;}
    .yellow{color:#facc15;}
    .blue{color:#38bdf8;}
    .red{color:#ef4444;}

    table{
        width:100%;
        border-collapse:collapse;
    }

    th,td{
        padding:10px;
        text-align:left;
        border-bottom:1px solid #1e293b;
    }

    th{color:#38bdf8;}

    .bottom-nav{
        position:fixed;
        bottom:0;
        left:0;
        width:100%;
        background:#0f172a;
        display:flex;
        justify-content:space-around;
        padding:12px;
        border-top:1px solid #1e293b;
    }

    .bottom-nav a{
        color:#94a3b8;
        text-decoration:none;
    }

    h3{
        color:#38bdf8;
    }
    </style>
    """


def topbar():
    return """
    <div class="topbar">
        <div class="logo">INDODAX AI BOT</div>
        <div class="subtitle">AI Trading Dashboard</div>
    </div>

    <div class="bottom-nav">
        <a href="/">🏠 Home</a>
        <a href="/scanner">📈 Scanner</a>
        <a href="/position">🤖 Bot</a>
        <a href="/history">📜 History</a>
    </div>
    """


@app.route("/")
def home():

    stats = get_stats()

    html = f"<html><head>{pwa()}{style()}</head><body>{topbar()}"

    html += f"""
    <div class="grid">

        <div class="card">
            <div class="title">TOTAL TRADES</div>
            <div class="value blue">{stats['total_trades']}</div>
        </div>

        <div class="card">
            <div class="title">WINRATE</div>
            <div class="value green">{stats['winrate']}%</div>
        </div>

        <div class="card">
            <div class="title">TOTAL PROFIT</div>
            <div class="value yellow">{stats['total_profit']}%</div>
        </div>

        <div class="card">
            <div class="title">BOT STATUS</div>
            <div class="value {'green' if BOT_RUNNING else 'red'}">
                {'RUNNING' if BOT_RUNNING else 'STOPPED'}
            </div>
        </div>

    </div>
    """

    html += "<h3>Market Overview</h3>"

    for coin in scanner.market_data[:5]:
        html += f"""
        <div class="card">
            {coin['symbol']} |
            {coin['signal']} |
            Score {coin['score']}
        </div>
        """

    html += "</body></html>"
    return html


@app.route("/start")
def start_bot():
    global BOT_RUNNING
    BOT_RUNNING = True
    trader.BOT_RUNNING = True
    scanner.BOT_RUNNING = True
    return redirect("/")


@app.route("/pause")
def pause_bot():
    global BOT_RUNNING
    BOT_RUNNING = False
    trader.BOT_RUNNING = False
    scanner.BOT_RUNNING = False
    return redirect("/")


@app.route("/stop")
def stop_bot():
    return pause_bot()


@app.route("/scanner")
def scanner_page():

    html = f"<html><head>{style()}</head><body>{topbar()}"
    html += "<h3>Scanner Premium</h3>"
    html += """
    <div class="table-box">
    <table>
    <tr>
        <th>Coin</th>
        <th>Signal</th>
        <th>Score</th>
        <th>RSI</th>
        <th>Price</th>
    </tr>
    """

    for coin in scanner.market_data:

        html += f"""
        <tr>
            <td>{coin['symbol']}</td>
            <td>{coin['signal']}</td>
            <td>{coin['score']}</td>
            <td>{coin['rsi']}</td>
            <td>{coin['price']}</td>
        </tr>
        """

    html += "</table></div></body></html>"
    return html


@app.route("/position")
def position_page():

    html = f"<html><head>{style()}</head><body>{topbar()}<h3>Position</h3>"

    if trader.active_trade:

        t = trader.active_trade

        html += f"""
        <div class="trade-box">
        <b>{t['symbol']}</b><br><br>

        Buy Price : {t.get('buy_price')}<br>
        Current Price : {t.get('current_price')}<br>
        TP Price : {t.get('tp_price')}<br>
        SL Price : {t.get('sl_price')}<br>
        Highest Price : {t.get('highest_price')}<br><br>

        Profit : {t.get('profit_percent')}%
        </div>
        """

    else:

        html += """
        <div class="trade-box">
        NO ACTIVE TRADE
        </div>
        """

    html += "</body></html>"
    return html


@app.route("/history")
def history_page():

    stats = get_stats()

    html = f"<html><head>{style()}</head><body>{topbar()}<h3>History</h3>"

    html += f"""
    <div class="grid">

        <div class="card">
            <div class="title">TOTAL TRADES</div>
            <div class="value blue">{stats['total_trades']}</div>
        </div>

        <div class="card">
            <div class="title">WINRATE</div>
            <div class="value green">{stats['winrate']}%</div>
        </div>

        <div class="card">
            <div class="title">TOTAL PROFIT</div>
            <div class="value yellow">{stats['total_profit']}%</div>
        </div>

    </div>
    """

    for t in stats["history"][:30]:
        html += f"""
        <div class="card">
        {t['symbol']} |
        {t['side']} |
        {t['profit_percent']}% |
        {t['time']}
        </div>
        """

    html += "</body></html>"
    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
