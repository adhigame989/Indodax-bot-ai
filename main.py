from flask import Flask, redirect, request
import ccxt
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import config
import trader
import scanner
import time

from scanner import start_scanner
from trader import start_trader, load_trades, active_trades
from history import get_stats
import history
import json

app = Flask(__name__)
from datetime import datetime

BOT_START_TIME = datetime.now()

BOT_STATUS = "PAUSED"

print("BOOTING BOT...")
load_trades()
print(f"LOADED {len(active_trades)} ACTIVE TRADES")
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
    .bottom-nav{position:fixed;bottom:0;left:0;width:100%;background:#0f172a;border-top:1px solid #1e293b;display:flex;justify-content:space-around;align-items:center;height:80px}
    .bottom-nav a{flex:1;text-align:center;color:#94a3b8;text-decoration:none;font-size:18px;padding:20px 0}
    .top-header{display:flex;justify-content:space-between;align-items:flex-start;}
    .datetime{text-align:right;color:#94a3b8;font-size:13px;line-height:1.5;}
    .creator{color:#38bdf8;margin-top:6px;}
    summary{cursor:pointer;font-weight:bold;list-style:none}
    summary::-webkit-details-marker{display:none}
    summary::before{content:"▶ ";color:#38bdf8}
    details[open] summary::before{content:"▼ "}
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
                <div class="subtitle">
                    Last Update: {now.strftime("%H:%M:%S")}
                </div>
            </div>

        </div>

    </div>

    <div class="bottom-nav">
        <a href="/">🏠 Home</a>
        <a href="/scanner">📈 Scanner</a>
        <a href="/position">📊 Positions</a>
        <a href="/history">📜 History</a>
        <a href="/settings">⚙️ Settings</a>
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
    
def rp(value):

    try:
        return f"Rp {float(value):,.0f}".replace(",", ".")

    except:
        return "Rp 0"
        
def fmt_amount(amount):

    try:
        return f"{float(amount):,.8f}".rstrip("0").rstrip(".")

    except:
        return "0"

def fmt_price(value):
    try:
        value = float(value)

        if value >= 1000:
            return f"{value:,.3f}".rstrip("0").rstrip(".").replace(",", ".")
        elif value >= 1:
            return f"{value:,.3f}".rstrip("0").rstrip(".").replace(",", ".")
        else:
            return f"{value:,.8f}".rstrip("0").rstrip(".").replace(",", ".")

    except:
        return "0"

def build_trade_bar(buy,current,tp,sl):
    try:
        buy=float(buy)
        current=float(current)
        tp=float(tp)
        sl=float(sl)

        if buy <= 0:
            return ""

        bar_color = "#22c55e"
        fill_width = 0
        fill_left = 50

        if current >= buy:
            progress=((current-buy)/(tp-buy))*50
            progress=max(0,min(progress,50))

            tp_confirm = buy + ((tp-buy)*0.75)

            if current >= tp_confirm:
                bar_color = "#38bdf8"

            fill_width = progress

        else:
            progress=((buy-current)/(buy-sl))*50
            progress=max(0,min(progress,50))

            bar_color = "#ef4444"
            fill_left = 50-progress
            fill_width = progress

        return f"""
        <div style="
        position:relative;
        width:100%;
        height:10px;
        background:#334155;
        border-radius:10px;
        overflow:hidden;
        margin-top:8px;
        margin-bottom:8px;
        ">
            <div style="
            position:absolute;
            left:{fill_left}%;
            width:{fill_width}%;
            height:100%;
            background:{bar_color};
            "></div>

            <div style="
            position:absolute;
            left:50%;
            top:0;
            width:2px;
            height:100%;
            background:white;
            "></div>
        </div>
        """
    except:
        return ""
        
def trade_metrics(t):

    buy = t.get("buy_price", 0)
    now = t.get("current_price", buy)

    high = t.get("highest_price", buy)
    low = t.get("lowest_price", buy)

    amount = t.get("amount", 0)

    current_rp = (now - buy) * amount
    high_rp = (high - buy) * amount
    low_rp = (low - buy) * amount

    high_pct = ((high - buy) / buy * 100) if buy else 0
    low_pct = ((low - buy) / buy * 100) if buy else 0

    hold = "-"

    if "buy_time" in t:

        sec = int(
            time.time() -
            t["buy_time"]
        )

        d = sec // 86400
        h = (sec % 86400) // 3600
        m = (sec % 3600) // 60

        hold = f"{d}d {h}h {m}m"

    return {
        "current_rp": current_rp,
        "high_rp": high_rp,
        "low_rp": low_rp,
        "high_pct": high_pct,
        "low_pct": low_pct,
        "hold": hold
    }


@app.route("/")
def home():
    stats = get_stats()
    uptime = get_uptime()
    win = stats["win"]
    loss = stats["loss"]
    now = datetime.now(
        ZoneInfo("Asia/Jakarta")
    ).strftime("%H:%M:%S")
    free_idr=0
    used_idr=0
    total_idr=0

    try:
        exchange=ccxt.indodax({
            'apiKey':config.API_KEY,
            'secret':config.SECRET_KEY,
            'enableRateLimit':True
        })

        balance=exchange.fetch_balance()
        print("FREE:", balance["free"].get("IDR", 0))
        print("USED:", balance["used"].get("IDR", 0))
        print("TOTAL:", balance["total"].get("IDR", 0))
        open_order_count = 0

        try:
            open_order_count = len(
                exchange.fetch_open_orders()
            )
        except:
            pass
        manual_positions = 0

        bot_symbols = {
            t["symbol"].split("/")[0]
            for t in trader.active_trades
        }
        for coin, amount in balance["total"].items():

            if coin == "IDR":
                continue

            if amount <= 0:
                continue

            if coin in bot_symbols:
                continue

            manual_positions += 1

        free_idr=balance['free'].get('IDR',0)
        used_idr=balance['used'].get('IDR',0)

        bot_coin_value = 0
        manual_coin_value = 0

        for coin, amount in balance['total'].items():

            if coin == "IDR":
                continue

            if amount <= 0:
                continue

            print("COIN:", coin, amount) 
            try:
                ticker = exchange.fetch_ticker(f"{coin}/IDR")
                price = ticker["last"]
                value = amount * price
                if coin in bot_symbols:
                    bot_coin_value += value
                else:
                    manual_coin_value += value
            except:
                pass

        total_idr = free_idr + used_idr + bot_coin_value + manual_coin_value
    except:
        pass

    profit_color = "yellow"
    layer_count = {}

    for t in trader.active_trades:
         symbol = t["symbol"]
         layer_count[symbol] = layer_count.get(symbol, 0) + 1

    if stats["total_profit"] > 0:
        profit_color = "green"
    elif stats["total_profit"] < 0:
        profit_color = "red"
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
          <div class="title">TOTAL ASSET</div>
          <div class="value green">Rp {total_idr:,.0f}</div>
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
        <div class="value {profit_color}">{stats['total_profit']}%
        </div>
        <div style="font-size:14px;margin-top:5px;color:#94a3b8;">{rp(stats.get('total_profit_idr',0))}
        </div>
      </div>

      <div class="card">
        <div class="title">WIN</div>
        <div class="value green">{win}</div>
      </div>

      <div class="card">
        <div class="title">LOSS</div>
        <div class="value red">{loss}</div>
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
    <details class="trade-box" open>
    <summary><b>MARKET STATUS</b></summary><br>
    <div style="display:flex;gap:20px;">
    <div style="flex:1;">

    BOT VALUE : Rp {bot_coin_value:,.0f}<br>
    MANUAL VALUE : Rp {manual_coin_value:,.0f}<br>
    ORDERS VALUE : Rp {used_idr:,.0f}<br>
    FREE IDR : Rp {free_idr:,.0f}<br>
    </div>
    <div style="flex:1;">
    UPTIME : {uptime}<br>

    TIMEFRAME : {config.TIMEFRAME}<br>

    SCANNED COINS : {len(scanner.market_data)}<br>
    BTC STATUS : {btc_view}
    </div>
    
    <div style="flex:1;">
    """
    unique_positions = len(layer_count)

    html += f"""
    BOT POSITIONS : {unique_positions}/{config.MAX_ACTIVE_TRADES}<br>
    """
    for symbol, count in layer_count.items():
        html += f"{symbol} : {count}/{config.MAX_LAYER_PER_COIN}<br>"

    html += f"""
    MANUAL POSITIONS : {manual_positions}<br>

    </div>
    </div>
    </details>
    """
    if trader.active_trades:

        grouped_trades = {}

        for t in trader.active_trades:
            symbol = t["symbol"]

            if symbol not in grouped_trades:
                grouped_trades[symbol] = []

            grouped_trades[symbol].append(t)

        html += """
        <details class="trade-box">
        <summary><b>BOT POSITIONS</b></summary><br>
        """

        for symbol, trades in grouped_trades.items():

            html += f"""
            <div class="trade-box">
            <h3>{symbol}</h3>

            <div style="
            display:flex;
            gap:12px;
            overflow-x:auto;
            padding-top:10px;
            ">
            """

            for t in trades:

                buy_score=t.get("buy_score",0)
                buy_reason=t.get("buy_reason","BUY")
                signal_color="green"
                if buy_reason=="STRONG BUY":
                    signal_color="blue"
                m = trade_metrics(t)

                color = "green"
                if t.get("profit_percent", 0) < 0:
                    color = "red"

                html += f"""
                <div style="
                min-width:240px;
                background:#1e293b;
                padding:15px;
                border-radius:14px;
                border:1px solid #334155;
                ">

                <div class="{color}"
                style="
                font-size:18px;
                font-weight:bold;
                margin-bottom:10px;
                ">
                Rp {t.get('current_value',0):,.0f}
                </div>
                <span class="{signal_color}">{buy_reason} ({buy_score})</span><br>

                Buy : Rp {fmt_price(t.get('buy_price'))}<br>
                Now : Rp {fmt_price(t.get('current_price'))}<br>

                <span class="{color}">
                P/L :
                Rp {m['current_rp']:,.0f}
                ({t.get('profit_percent')}%)
                </span>
                <br>

                {build_trade_bar(
                    t.get("buy_price"),
                    t.get("current_price"),
                    t.get("tp_price"),
                    t.get("sl_price")
                )}

                Hold : {m['hold']}

                </div>
                """

            html += """
            </div>
            </div>
            """

        html += "</details>"

    if manual_positions > 0:

        html += """
        <details class="trade-box">
        <summary><h3 style="display:inline;">MANUAL POSITIONS</h3></summary>

        <div style="
        display:flex;
        gap:12px;
        overflow-x:auto;
        padding-top:10px;
        ">
        """

        for coin, amount in balance["total"].items():

            if coin == "IDR":
                continue

            if amount <= 0:
                continue

            if coin in bot_symbols:
                continue

            try:
                ticker = exchange.fetch_ticker(f"{coin}/IDR")
                price = ticker["last"]
                value = amount * price

                html += f"""
                <div style="
                min-width:260px;
                background:#1e293b;
                padding:15px;
                border-radius:14px;
                border:1px solid #334155;
                ">

                <div class="blue"
                style="
                font-size:18px;
                font-weight:bold;
                margin-bottom:10px;
                ">
                Rp {value:,.0f}
                </div>

                Coin : {coin}<br>
                Amount : {fmt_amount(amount)}<br>
                Now : Rp {fmt_price(price)}<br><br>

                <span class="yellow">
                Status : Holding
                </span>

                </div>
                """

            except:
                pass

        html += "</div></details>"
    html += """
    <details class='trade-box'>
    <summary><b>TOP SIGNALS & BEST SIGNAL</b></summary><br>
    <div style="display:flex;gap:20px;">
    <div style="flex:2;">
    <b>TOP SIGNALS</b><br><br>
    """

    for i, coin in enumerate(scanner.market_data[:10], start=1):
        html += f"#{i} {coin['symbol']} | {coin['signal']} | Score {coin['score']}<br>"

    html += "</div>"

    if scanner.market_data:
        top = scanner.market_data[0]

        html += f"""
        <div style="flex:1;">
        <b>BEST SIGNAL NOW</b><br><br>

        Coin : {top['symbol']}<br>
        Signal : {top['signal']}<br>
        Score : {top['score']}<br>
        RSI : {top['rsi']}
        </div>
        """

    html += """
    </div>
    </details>
    """

    html += """
    <script>
    function updateClock(){const now=new Date();const d=document.getElementById("live-date");const c=document.getElementById("live-clock");if(d)d.innerHTML=now.toLocaleDateString('id-ID');if(c)c.innerHTML=now.toLocaleTimeString('id-ID')+" WIB";}
    updateClock();
    setInterval(updateClock,1000);
    document.addEventListener("DOMContentLoaded",function(){document.querySelectorAll("details").forEach((fold,index)=>{const key="fold_"+index;if(localStorage.getItem(key)==="open")fold.setAttribute("open",true);fold.addEventListener("toggle",function(){if(fold.open){localStorage.setItem(key,"open")}else{localStorage.removeItem(key)}});});});
    </script>
    """
    html += auto_refresh()
    html += "</body></html>"
    return html


@app.route("/start")
def start_bot():
    global BOT_STATUS
    BOT_STATUS = "RUNNING"
    trader.BOT_RUNNING = True
    trader.BUY_ENABLED = True
    scanner.BOT_RUNNING = True
    return redirect("/")


@app.route("/pause")
def pause_bot():
    global BOT_STATUS
    BOT_STATUS = "PAUSED"
    trader.BOT_RUNNING = True
    trader.BUY_ENABLED = False
    scanner.BOT_RUNNING = True
    return redirect("/")


@app.route("/stop")
def stop_bot():
    global BOT_STATUS
    BOT_STATUS = "STOPPED"
    trader.BOT_RUNNING = False
    trader.BUY_ENABLED = False
    scanner.BOT_RUNNING = False
    return redirect("/")

@app.route("/manual_sell/<trade_id>")
def manual_sell_route(trade_id):
    trader.manual_sell(trade_id)

    return redirect("/position")

    
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
    html = f"<html><head>{style()}</head><body>{topbar()}"

    if trader.active_trades:

        grouped_trades = {}

        for t in trader.active_trades:
            symbol = t["symbol"]

            if symbol not in grouped_trades:
                grouped_trades[symbol] = []

            grouped_trades[symbol].append(t)

        for symbol, trades in grouped_trades.items():

            html += f"""
            <div class='trade-box'>
            <h3>{symbol}</h3>

            <div style="
            display:flex;
            gap:12px;
            overflow-x:auto;
            padding-top:10px;
            ">
            """

            for i, t in enumerate(trades):

                m = trade_metrics(t)
                buy_score=t.get("buy_score",0)
                buy_reason=t.get("buy_reason","-")

                p = "green"

                if t.get("profit_percent", 0) < 0:
                    p = "red"

                html += f"""
                <div style="
                min-width:260px;
                background:#1e293b;
                padding:15px;
                border-radius:14px;
                border:1px solid #334155;
                ">

                <b>{symbol.split('/')[0]} #{i+1}</b><br><br>

                Buy : Rp {fmt_price(t.get('buy_price'))}<br>
                Now : Rp {fmt_price(t.get('current_price'))}<br><br>
                Reason : {buy_reason}<br>
                Score : {buy_score}<br><br>
                Amount : {fmt_amount(t.get('amount',0))}<br>

                Modal : Rp {t.get('entry_value', 0):,.0f}<br>
                Value : Rp {t.get('current_value', t.get('trade_amount', 0)):,.0f}<br><br>

                High : Rp {m['high_rp']:,.0f} ({m['high_pct']:.2f}%)<br>
                Low : Rp {m['low_rp']:,.0f} ({m['low_pct']:.2f}%)<br>

                <span class='{p}'>

                Current : Rp {m['current_rp']:,.0f}
                ({t.get('profit_percent')}%)

                </span>

                <br><br>

                TP : Rp {fmt_price(t.get('tp_price'))}<br>
                SL : Rp {fmt_price(t.get('sl_price'))}<br>
                Hold : {m['hold']}<br><br>

                <a href="javascript:void(0)"
                onclick="if(confirm('Yakin mau sell {symbol.split('/')[0]} layer #{i+1}?')) window.location='/manual_sell/{t.get('id')}';"
                style="
                display:inline-block;
                padding:10px 15px;
                background:#991b1b;
                color:white;
                border-radius:10px;
                text-decoration:none;
                font-weight:bold;
                ">
                SELL
                </a>

                </div>
                """

            html += "</div></div>"

    else:
        html += "<div class='trade-box'>NO ACTIVE TRADE</div>"

    html += "</body></html>"

    return html


@app.route("/history")
def history_page():
    stats=get_stats()
    html=f"<html><head>{style()}</head><body>{topbar()}"
    analytics = stats.get("analytics", {})

    tp_count = analytics.get("tp_count", 0)
    sl_count = analytics.get("sl_count", 0)
    trail_count = analytics.get("trail_count", 0)
    manual_count = analytics.get("manual_count", 0)

    buy_wr = analytics.get("buy_winrate", 0)
    strong_wr = analytics.get("strong_buy_winrate", 0)

    avg_win = analytics.get("avg_win_score", 0)
    avg_loss = analytics.get("avg_loss_score", 0)
    buy_tp = analytics.get("buy_tp", 0)
    buy_sl = analytics.get("buy_sl", 0)
    buy_trail = analytics.get("buy_trail", 0)

    strong_tp = analytics.get("strong_tp", 0)
    strong_sl = analytics.get("strong_sl", 0)
    strong_trail = analytics.get("strong_trail", 0)
    score_buckets=stats.get("score_buckets",{})

    b80=score_buckets.get("80_89",{})
    b90=score_buckets.get("90_99",{})
    b100=score_buckets.get("100_109",{})
    b110=score_buckets.get("110_119",{})
    b120=score_buckets.get("120_plus",{})

    b80_total=b80.get("win",0)+b80.get("loss",0)
    b90_total=b90.get("win",0)+b90.get("loss",0)
    b100_total=b100.get("win",0)+b100.get("loss",0)
    b110_total=b110.get("win",0)+b110.get("loss",0)
    b120_total=b120.get("win",0)+b120.get("loss",0)

    b80_wr=round((b80.get("win",0)/b80_total)*100,2) if b80_total>0 else 0
    b90_wr=round((b90.get("win",0)/b90_total)*100,2) if b90_total>0 else 0
    b100_wr=round((b100.get("win",0)/b100_total)*100,2) if b100_total>0 else 0
    b110_wr=round((b110.get("win",0)/b110_total)*100,2) if b110_total>0 else 0
    b120_wr=round((b120.get("win",0)/b120_total)*100,2) if b120_total>0 else 0

    avg_hold=stats.get("avg_hold",0)
    fastest_tp=stats.get("fastest_tp",0)
    longest_hold=stats.get("longest_hold",0)
    avg_profit=stats.get("avg_profit",0)

    avg_hold_fmt=f"{int(avg_hold//86400)}d {int((avg_hold%86400)//3600)}h" if avg_hold>=86400 else f"{int(avg_hold//3600)}h {int((avg_hold%3600)//60)}m"
    fastest_tp_fmt=f"{int(fastest_tp//86400)}d {int((fastest_tp%86400)//3600)}h" if fastest_tp>=86400 else f"{int(fastest_tp//3600)}h {int((fastest_tp%3600)//60)}m"
    longest_hold_fmt=f"{int(longest_hold//86400)}d {int((longest_hold%86400)//3600)}h" if longest_hold>=86400 else f"{int(longest_hold//3600)}h {int((longest_hold%3600)//60)}m"
    
    html+=f"""
    <div class='grid'>
      <div class='card'><div class='title'>TOTAL TRADES</div><div class='value blue'>{stats['total_trades']}</div></div>
      <div class='card'><div class='title'>WINRATE</div><div class='value green'>{stats['winrate']}%</div></div>
      <div class='card'><div class='title'>TOTAL PROFIT</div><div class='value yellow'>{stats['total_profit']}%</div></div>
    </div>
    """
    html += f"""
    <div class="trade-box">

    <div style="display:flex;gap:15px;flex-wrap:wrap;">

    <div style="flex:1;">
    <b>📊 TRADE REASON</b><br><br>

    TP : {tp_count}<br>
    SL : {sl_count}<br>
    TRAIL : {trail_count}<br>
    MANUAL : {manual_count}<br><br>
    STRONG WR : {strong_wr}%<br>
    BUY WR : {buy_wr}%<br><br>
    AVG WIN : {avg_win}<br>
    AVG LOSS : {avg_loss}
    </div>

    <div style="flex:1;">
    <b>📈 REASON PERFORMANCE</b><br><br>

    STRONG → TP : {strong_tp}<br>
    STRONG → SL : {strong_sl}<br>
    STRONG → TRAIL : {strong_trail}<br><br>
    BUY → TP : {buy_tp}<br>
    BUY → SL : {buy_sl}<br>
    BUY → TRAIL : {buy_trail}
    </div>

    <div style="flex:1;">
    <b>📶 SCORE BUCKET</b><br><br>

    80-89 : {b80_total} | {b80_wr}%<br>
    90-99 : {b90_total} | {b90_wr}%<br>
    100-109 : {b100_total} | {b100_wr}%<br>
    110-119 : {b110_total} | {b110_wr}%<br>
    120+ : {b120_total} | {b120_wr}%
    </div>
    <div style="flex:1;">
    <b>⏱ CAPITAL EFFICIENCY</b><br><br>

    AVG HOLD : {avg_hold_fmt}<br>
    FASTEST TP : {fastest_tp_fmt}<br>
    LONGEST : {longest_hold_fmt}<br>
    AVG PROFIT : {avg_profit}%
    </div>
    </div>
    </div>
    """

    html += """
        <div class="trade-box">
        <a href="javascript:void(0)"
        onclick="if(confirm('Reset semua history? Active trade tetap aman.')) window.location='/reset_history';"
        style="
        display:inline-block;
        padding:12px 18px;
        background:#991b1b;
        color:white;
        border-radius:12px;
        text-decoration:none;
        font-weight:bold;
        ">
        🗑 RESET HISTORY
        </a>
        </div>
        """
    for t in stats['history'][:30]:

        waktu = t['time']

        try:

            from datetime import datetime

            dt = datetime.fromisoformat(
                waktu
            )

            waktu = dt.strftime(
                "%d-%m-%Y %H:%M WIB"
            )

        except:
            pass
        reason = t.get("reason","-")
        buy_reason = t.get("buy_reason","-")
        buy_score = t.get("buy_score","-")

        trade_type = t["side"]

        if trade_type == "SELL" and reason:
            trade_type = f"{trade_type} ({reason})"

        buy_info = f"{buy_reason} ({buy_score})"

        html += (
            f"<div class='card'>"
            f"{t['symbol']} | "
            f"{buy_info} | "
            f"{trade_type} | "
            f"{t['profit_percent']}% | "
            f"{waktu}"
            f"</div>"
        )
    html+="</body></html>"
    return html

@app.route("/reset_history")
def reset_history():

    try:

        with open(history.HISTORY_FILE, "w") as f:
            json.dump([], f)

        print("HISTORY RESET")

    except Exception as e:

        print("RESET ERROR:", str(e))

    return redirect("/history")
    
@app.route("/settings")
def settings_page():

    html = f"""
    <html>
    <head>{style()}</head>
    <body>

    {topbar()}

    <div class="trade-box">

    <h2>⚙️ BOT SETTINGS</h2>

    <form action="/save_settings" method="post">

    Base Trade Amount<br>
    <input type="number" name="base_trade_amount"
    value="{config.BASE_TRADE_AMOUNT}"><br><br>

    Bot Capital Limit<br>
    <input type="number" name="bot_capital_limit"
    value="{config.BOT_CAPITAL_LIMIT}"><br><br>

    Max Active Trades<br>
    <input type="number" name="max_active_trades"
    value="{config.MAX_ACTIVE_TRADES}"><br><br>

    Max Layer Per Coin<br>
    <input type="number" name="max_layer_per_coin"
    value="{config.MAX_LAYER_PER_COIN}"><br><br>

    Take Profit (%)<br>
    <input type="number" step="0.1"
    name="take_profit"
    value="{config.TAKE_PROFIT}"><br><br>

    Stop Loss (%)<br>
    <input type="number" step="0.1"
    name="stop_loss"
    value="{config.STOP_LOSS}"><br><br>

    Trailing Gap (%)<br>
    <input type="number" step="0.1"
    name="trailing_gap"
    value="{config.TRAILING_GAP}"><br><br>

    Scan Limit<br>
    <input type="number"
    name="scan_limit"
    value="{config.SCAN_LIMIT}"><br><br>

    <button type="submit">
    SAVE SETTINGS
    </button>

    </form>

    </div>

    </body>
    </html>
    """

    return html
@app.route("/save_settings", methods=["POST"])
def save_settings():

    config.BASE_TRADE_AMOUNT = int(request.form["base_trade_amount"])

    config.BOT_CAPITAL_LIMIT = int(request.form["bot_capital_limit"])

    config.MAX_ACTIVE_TRADES = int(request.form["max_active_trades"])

    config.MAX_LAYER_PER_COIN = int(request.form["max_layer_per_coin"])

    config.TAKE_PROFIT = float(request.form["take_profit"])

    config.STOP_LOSS = float(request.form["stop_loss"])

    config.TRAILING_GAP = float(request.form["trailing_gap"])

    config.SCAN_LIMIT = int(request.form["scan_limit"])

    return redirect("/settings")

if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
