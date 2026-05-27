from flask import Flask
import ccxt
import config
from scanner import scan_market

app = Flask(__name__)

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

        markets = scan_market()

        html = f"""
        <html>

        <head>

        <title>INDODAX AI BOT</title>

        <style>

        body {{
            background:#0f172a;
            color:white;
            font-family:Arial;
            padding:20px;
        }}

        .card {{
            background:#1e293b;
            padding:15px;
            margin-bottom:10px;
            border-radius:12px;
        }}

        h1 {{
            color:#38bdf8;
        }}

        </style>

        </head>

        <body>

        <h1>INDODAX AI BOT</h1>

        <div class="card">
            <h2>Status: ONLINE</h2>
            <h3>Saldo IDR: Rp {idr:,.0f}</h3>
        </div>
        """

        for coin in markets:

            html += f"""
            <div class="card">

                <h3>{coin['symbol']}</h3>

                <p>Price: {coin['price']}</p>

                <p>Volume: {coin['volume']:,.0f}</p>

                <p>24H Change: {coin['change']}%</p>

                <p>Spread: {coin['spread']:.2f}%</p>

            </div>
            """

        html += """
        </body>
        </html>
        """

        return html

    except Exception as e:

        return f"<h1>ERROR</h1><pre>{str(e)}</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
