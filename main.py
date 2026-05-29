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
    """

def style():
    return "<style>body{background:#020617;color:white;font-family:Arial;padding:20px}.card,.trade-box{background:#111827;padding:15px;border-radius:15px;margin:10px 0}table{width:100%}td,th{padding:8px}</style>"

def topbar():
    return """
    <h2>INDODAX AI BOT</h2>
    <a href="/">Home</a> |
    <a href="/scanner">Scanner</a> |
    <a href="/position">Bot</a> |
    <a href="/history">History</a><hr>
    """

@app.route("/")
def home():
    stats = get_stats()
    html=f"<html><head>{style()}{pwa()}</head><body>{topbar()}"
    html+=f"<div class='card'>Trades: {stats['total_trades']} | Winrate: {stats['winrate']}%</div>"
    html+="<h3>Market Overview</h3>"
    for coin in scanner.market_data[:5]:
        html+=f"<div class='card'>{coin['symbol']} - {coin['signal']} - Score {coin['score']}</div>"
    html+="</body></html>"
    return html

@app.route("/start")
def start_bot():
    global BOT_RUNNING
    BOT_RUNNING=True
    trader.BOT_RUNNING=True
    scanner.BOT_RUNNING=True
    return redirect("/")

@app.route("/pause")
def pause_bot():
    global BOT_RUNNING
    BOT_RUNNING=False
    trader.BOT_RUNNING=False
    scanner.BOT_RUNNING=False
    return redirect("/")

@app.route("/stop")
def stop_bot():
    return pause_bot()

@app.route("/scanner")
def scanner_page():
    html=f"<html><head>{style()}</head><body>{topbar()}<h3>Scanner Premium</h3><table border=1><tr><th>Coin</th><th>Signal</th><th>Score</th><th>RSI</th></tr>"
    for coin in scanner.market_data:
        html+=f"<tr><td>{coin['symbol']}</td><td>{coin['signal']}</td><td>{coin['score']}</td><td>{coin['rsi']}</td></tr>"
    html+="</table></body></html>"
    return html

@app.route("/position")
def position_page():
    html=f"<html><head>{style()}</head><body>{topbar()}"
    if trader.active_trade:
        t=trader.active_trade
        html+=f"<div class='trade-box'>{t['symbol']}<br>Buy:{t['buy_price']}<br>Current:{t['current_price']}<br>Profit:{t['profit_percent']}%</div>"
    else:
        html+="<div class='trade-box'>NO ACTIVE TRADE</div>"
    html+="</body></html>"
    return html

@app.route("/history")
def history_page():
    stats=get_stats()
    html=f"<html><head>{style()}</head><body>{topbar()}<h3>History</h3>"
    for t in stats['history'][:30]:
        html+=f"<div class='card'>{t['symbol']} | {t['side']} | {t['profit_percent']}%</div>"
    html+="</body></html>"
    return html

if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
