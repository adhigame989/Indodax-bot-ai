from flask import Flask, redirect
import ccxt
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import config
import trader
import scanner

from scanner import start_scanner
from trader import start_trader
from history import get_stats

app = Flask(__name__)
from datetime import datetime

BOT_START_TIME = datetime.now()

BOT_RUNNING = False
BOT_STATUS = "STOPPED"

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
    body{background:#020617;color:white;font-family:Arial,sans-serif;margin:0;padding:15px;padding-bottom:90px}
    .topbar{background:#0f172a;padding:20px;border-radius:20px;border:1px solid #1e293b;margin-bottom:15px}
    .logo{font-size:28px;font-weight:bold;color:#38bdf8}
    .subtitle{color:#94a3b8}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
    .card,.trade-box,.table-box{background:#0f172a;border:1px solid #1e293b;border-radius:18px;padding:15px;margin-bottom:12px}
    .title{color:#94a3b8;font-size:12px}
    .value{font-size:24px;font-weight:bold}
    .green{color:#22c55e}.red{color:#ef4444}.yellow{color:#facc15}.blue{color:#38bdf8}
    .btns{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:15px}
    .btn{padding:12px;border-radius:12px;text-align:center;color:white;text-decoration:none;font-weight:bold}
    .start{background:#166534}.pause{background:#854d0e}.stop{background:#991b1b}
    table{width:100%;border-collapse:collapse}
    th,td{padding:10px;border-bottom:1px solid #1e293b;text-align:left}
    th{color:#38bdf8}
    .bottom-nav{position:fixed;bottom:0;left:0;width:100%;background:#0f172a;border-top:1px solid #1e293b;display:flex;justify-content:space-around;padding:12px}
    .bottom-nav a{color:#94a3b8;text-decoration:none}
    .top-header{display:flex;justify-content:space-between;align-items:flex-start;}
    .datetime{text-align:right;color:#94a3b8;font-size:13px;line-height:1.5;}
    .creator{color:#38bdf8;margin-top:6px;}
    </style>
    """


def topbar():

    now = datetime.now(
        ZoneInfo("Asia/Jakarta")
    )

    tanggal = now.strftime(
        "%d-%m-%Y"
    )

    jam = now.strftime(
        "%H:%M:%S WIB"
    )

    return f"""
    <div class="topbar">

        <div class="top-header">

            <div>

                <div class="logo">
                    INDODAX AI BOT
                </div>

                <div class="subtitle">
                    Premium Dashboard V3.6
                </div>

                <div class="creator">
                    By: Adhi Prasetyo
                </div>

            </div>

            <div class="datetime">
                <div id="live-date"></div>
                <div id="live-clock"></div>
            </div>

        </div>

    </div>

    <div class="bottom-nav">
        <a href="/">🏠 Home</a>
        <a href="/scanner">📈 Scanner</a>
        <a href="/position">🤖 Bot</a>
        <a href="/history">📜 History</a>
    </div>
    """


def auto_refresh():
    return """
    <script>
    setTimeout(function(){location.reload();},10000);
    </script>
    """
    
def get_uptime():

    delta = datetime.now() - BOT_START_TIME

    days = delta.days

    hours = delta.seconds // 3600

    minutes = (
        delta.seconds % 3600
    ) // 60

    return (
        f"{days}d "
        f"{hours}h "
        f"{minutes}m"
    )


@app.route("/")
def home():
    stats = get_stats()
    uptime = get_uptime()
    win = stats["win"]
    loss = stats["loss"]
    now = datetime.now(
        ZoneInfo("Asia/Jakarta")
    ).strftime("%H:%M:%S")
    wallet = 0
    try:
        exchange = ccxt.indodax({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'enableRateLimit': True
        })
        balance = exchange.fetch_balance()
        wallet = balance['total'].get('IDR',0)
    except:
        pass

    html = f"<html><head>{pwa()}{style()}</head><body>{topbar()}"

    html += """
    <div class="btns">
        <a class="btn start" href="/start">START</a>
        <a class="btn pause" href="/pause">PAUSE</a>
        <a class="btn stop" href="/stop">STOP</a>
    </div>
    """

    if BOT_STATUS == "RUNNING":
        status_text = "🟢 BOT RUNNING"
        status_class = "green"

    elif BOT_STATUS == "PAUSED":
        status_text = "🟡 BOT PAUSED"
        status_class = "yellow"

    else:
        status_text = "🔴 BOT STOPPED"
        status_class = "red"

    html += f"""
    <div class="trade-box">
        <div class="value {status_class}">{status_text}</div>
    </div>
    """

    html += f"""
    <div class="grid">

      <div class="card">
        <div class="title">WALLET</div>
        <div class="value green">Rp {wallet:,.0f}</div>
      </div>

      <div class="card">
        <div class="title">TRADES</div>
        <div class="value blue">{stats['total_trades']}</div>
      </div>

      <div class="card">
        <div class="title">WINRATE</div>
        <div class="value green">{stats['winrate']}%</div>
      </div>

      <div class="card">
        <div class="title">PROFIT</div>
        <div class="value yellow">{stats['total_profit']}%</div>
      </div>

      <div class="card">
        <div class="title">WIN</div>
        <div class="value green">{win}</div>
      </div>

      <div class="card">
        <div class="title">LOSS</div>
        <div class="value red">{loss}</div>
      </div>

      <div class="card">
        <div class="title">LAST UPDATE</div>
        <div class="value blue">{now}</div>
      </div>

    </div>
    """

    btc_status = scanner.check_btc_market()
    if btc_status == "BULLISH":

        btc_view = "🟢 BULLISH"

    elif btc_status == "NEUTRAL":

        btc_view = "🟡 NEUTRAL"

    else:

        btc_view = "🔴 PANIC"
    
    html += f"""
    <div class="trade-box">
    <b>MARKET STATUS</b><br><br>

    BOT : {BOT_STATUS}<br>

    UPTIME : {uptime}<br>

    TIMEFRAME : {config.TIMEFRAME}<br>

    SCANNED COINS : {len(scanner.market_data)}<br>

    BTC STATUS : {btc_view}

    </div>
    """
    if trader.active_trade:

        t = trader.active_trade

        color = "green"

        if t.get("profit_percent", 0) < 0:
            color = "red"

        html += f"""
        <div class="trade-box">

        <b>ACTIVE POSITION</b><br><br>

        Coin : {t['symbol']}<br>
        Buy : {t['buy_price']}<br>

        <span class="{color}">
        Profit : {t['profit_percent']}%
        </span>

        </div>
        """

    else:

        html += """
        <div class="trade-box">

        <b>ACTIVE POSITION</b><br><br>

        NO ACTIVE TRADE

        </div>
        """

    html += "<div class='trade-box'><b>TOP SIGNALS</b><br><br>"
    for i, coin in enumerate(scanner.market_data[:10], start=1):
        html += f"#{i} {coin['symbol']} | {coin['signal']} | Score {coin['score']}<br>"
    html += "</div>"
    if scanner.market_data:

        top = scanner.market_data[0]

        html += f"""
        <div class="trade-box">

        <b>BEST SIGNAL NOW</b><br><br>

        Coin : {top['symbol']}<br>
        Signal : {top['signal']}<br>
        Score : {top['score']}<br>
        RSI : {top['rsi']}

        </div>
        """

    html += """
    <script>
    function updateClock(){
    const now=new Date();
    const d=document.getElementById("live-date");
    const c=document.getElementById("live-clock");
    if(d){d.innerHTML=now.toLocaleDateString('id-ID');}
    if(c){c.innerHTML=now.toLocaleTimeString('id-ID')+" WIB";}
    }
    updateClock();
    setInterval(updateClock,1000);
    </script>
    """
    html += auto_refresh()
    html += "</body></html>"
    return html


@app.route("/start")
def start_bot():
    global BOT_RUNNING
    global BOT_STATUS
    BOT_RUNNING=True
    BOT_STATUS = "RUNNING"
    trader.BOT_RUNNING=True
    scanner.BOT_RUNNING=True
    return redirect("/")


@app.route("/pause")
def pause_bot():
    global BOT_RUNNING
    global BOT_STATUS
    BOT_RUNNING=True
    BOT_STATUS = "PAUSED"
    trader.BOT_RUNNING=False
    scanner.BOT_RUNNING=True
    return redirect("/")


@app.route("/stop")
def stop_bot():
    global BOT_RUNNING
    global BOT_STATUS
    BOT_RUNNING = False
    BOT_STATUS = "STOPPED"
    scanner.BOT_RUNNING = False
    trader.BOT_RUNNING = False
    return redirect("/")


@app.route("/scanner")
def scanner_page():
    html=f"<html><head>{style()}</head><body>{topbar()}<div class='table-box'><table><tr><th>Coin</th><th>Signal</th><th>Score</th><th>RSI</th><th>Price</th></tr>"
    for c in scanner.market_data:
        color=""
        if c['signal']=="BUY" or c['signal']=="STRONG BUY":
            color="green"
        elif c['signal']=="WATCH":
            color="yellow"
        html+=f"<tr><td>{c['symbol']}</td><td class='{color}'>{c['signal']}</td><td>{c['score']}</td><td>{c['rsi']}</td><td>{c['price']}</td></tr>"
    html+="</table></div>"+auto_refresh()+"</body></html>"
    return html


@app.route("/position")
def position_page():
    html=f"<html><head>{style()}</head><body>{topbar()}"
    if trader.active_trade:
        t=trader.active_trade
        p="green" if t.get('profit_percent',0)>=0 else "red"
        html+=f"""
        <div class='trade-box'>
        <b>{t.get('symbol')}</b><br><br>
        Buy Price : {t.get('buy_price')}<br>
        Current Price : {t.get('current_price')}<br>
        TP Price : {t.get('tp_price')}<br>
        SL Price : {t.get('sl_price')}<br>
        Highest Price : {t.get('highest_price')}<br><br>
        <span class='{p}'>Profit : {t.get('profit_percent')}%</span>
        </div>
        """
    else:
        html+="<div class='trade-box'>NO ACTIVE TRADE</div>"
    html+="</body></html>"
    return html


@app.route("/history")
def history_page():
    stats=get_stats()
    html=f"<html><head>{style()}</head><body>{topbar()}"
    html+=f"""
    <div class='grid'>
      <div class='card'><div class='title'>TOTAL TRADES</div><div class='value blue'>{stats['total_trades']}</div></div>
      <div class='card'><div class='title'>WINRATE</div><div class='value green'>{stats['winrate']}%</div></div>
      <div class='card'><div class='title'>TOTAL PROFIT</div><div class='value yellow'>{stats['total_profit']}%</div></div>
    </div>
    """
    for t in stats['history'][:30]:
        html+=f"<div class='card'>{t['symbol']} | {t['side']} | {t['profit_percent']}% | {t['time']}</div>"
    html+="</body></html>"
    return html


if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
