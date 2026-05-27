from flask import Flask
import ccxt
import config

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

        return f"""
        <html>

        <body style="
            background:#0f172a;
            color:white;
            font-family:Arial;
            padding:20px;
        ">

        <h1>INDODAX AI BOT</h1>

        <h2>BOT ONLINE</h2>

        <h3>Saldo IDR:</h3>

        <h1>Rp {idr:,.0f}</h1>

        </body>

        </html>
        """

    except Exception as e:

        return f"<pre>{str(e)}</pre>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
