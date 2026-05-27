from flask import Flask
import ccxt
import config

app = Flask(__name__)

exchange = ccxt.indodax({
    'apiKey': config.API_KEY,
    'secret': config.SECRET_KEY
})

@app.route("/")
def home():

    try:
        balance = exchange.fetch_balance()

        idr = balance['total'].get('IDR', 0)

        html = f"""
        <h1>INDODAX AI BOT</h1>

        <h2>Bot Status: ONLINE</h2>

        <h3>Saldo IDR:</h3>
        <p>Rp {idr:,.0f}</p>
        """

        return html

    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
