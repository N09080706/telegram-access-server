from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

BOT_TOKEN = "8207091935:AAGW2v1pbhycjGOQEbdzqAlvQts-MfRyo4I"
ADMIN_ID = 7849292154

allowed_file = "allowed.json"


def load_allowed():
    try:
        with open(allowed_file) as f:
            return json.load(f)
    except:
        return {}


def save_allowed(data):
    with open(allowed_file, "w") as f:
        json.dump(data, f)


@app.route("/request_access", methods=["POST"])
def request_access():

    data = request.json

    name = data["name"]
    device = data["device"]

    text = f"Запрос доступа\n\nИмя: {name}\nID: {device}"

    keyboard = {
        "inline_keyboard":[
            [
                {"text":"Разрешить","callback_data":f"allow:{device}"},
                {"text":"Запретить","callback_data":f"deny:{device}"}
            ]
        ]
    }

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": ADMIN_ID,
            "text": text,
            "reply_markup": keyboard
        }
    )

    return {"status":"pending"}


@app.route("/check/<device>")
def check(device):

    allowed = load_allowed()

    if device in allowed:
        return {"allowed":True}

    return {"allowed":False}


app.run(host="0.0.0.0", port=8080)

@app.route("/telegram", methods=["POST"])
def telegram():

    update = request.json

    if "callback_query" in update:

        data = update["callback_query"]["data"]
        device = data.split(":")[1]

        allowed = load_allowed()

        if data.startswith("allow"):

            allowed[device] = True
            save_allowed(allowed)

            text = "Доступ разрешён"

        else:

            if device in allowed:
                del allowed[device]
                save_allowed(allowed)

            text = "Доступ запрещён"

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            json={
                "callback_query_id": update["callback_query"]["id"],
                "text": text
            }
        )

    return "ok"
