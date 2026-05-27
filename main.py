from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>INDODAX AI BOT</h1>
    <p>Bot Running...</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
