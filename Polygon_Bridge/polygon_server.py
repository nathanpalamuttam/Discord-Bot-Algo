from flask import Flask, request, jsonify
from polygon import RESTClient
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../.env")
app = Flask(__name__)
API_KEY = os.environ.get("API_KEY_POLYGON")

client = RESTClient(API_KEY)

@app.route("/vwap", methods=["POST"])
def get_vwap():
    data = request.get_json()
    symbol = data.get("symbol")
    from_date = data.get("from")
    to_date = data.get("to")

    try:
        agg = client.get_aggs(
            ticker=symbol,
            multiplier=1,
            timespan="minute",
            from_=from_date,
            to=to_date,
            limit=50000
        )
        total_price_volume = sum([bar.vwap * bar.volume for bar in agg])
        total_volume = sum([bar.volume for bar in agg])
        vwap = total_price_volume / total_volume if total_volume else 0

        return jsonify({"vwap": vwap, "volume": total_volume})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)