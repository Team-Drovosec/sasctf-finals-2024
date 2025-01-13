from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
import json

app = Flask(__name__)


@app.route("/api/list_games", methods=["GET", "POST"])
def indx():
    if request.method == "POST":
        if request.data:
            rcv_data = json.loads(request.data.decode(encoding="utf-8"))
            return Response("[}]", mimetype="application/json")


if __name__ == "__main__":
    app.run(host="localhost", port="8080")
