from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

BOT_TOKEN = "8207091935:AAGW2v1pbhycjGOQEbdzqAlvQts-MfRyo4I"
ADMIN_ID = 7849292154

ALLOWED_FILE = "allowed.json"


def load_allowed():
    try:
        with open(ALLOWED_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_allowed(data):
    with open(ALLOWED_FILE, "w") as f:
        json.dump(data, f)


def send_message(text, keyboard=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": ADMIN_ID,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(url, json=data)


@app.route("/request_access", methods=["POST"])
def request_access():

    data = request.json

    name = data["name"]
    device = data["device"]

    text = f"Запрос доступа\n\nИмя: {name}\nDevice: {device}"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Разрешить", "callback_data": f"allow:{device}:{name}"},
                {"text": "Запретить", "callback_data": f"deny:{device}"}
            ]
        ]
    }

    send_message(text, keyboard)

    return {"status": "pending"}


@app.route("/check/<device>")
def check(device):

    allowed = load_allowed()

    if device in allowed:
        return {"allowed": True}

    return {"allowed": False}


@app.route("/telegram", methods=["POST"])
def telegram():

    update = request.json

    # обработка кнопок
    if "callback_query" in update:

        data = update["callback_query"]["data"]

        allowed = load_allowed()

        if data.startswith("allow"):

            _, device, name = data.split(":")

            allowed[device] = name
            save_allowed(allowed)

            text = f"Доступ разрешён\n{name}"

        elif data.startswith("deny"):

            device = data.split(":")[1]

            if device in allowed:
                del allowed[device]
                save_allowed(allowed)

            text = "Доступ запрещён"

        elif data.startswith("remove"):

            device = data.split(":")[1]

            if device in allowed:
                del allowed[device]
                save_allowed(allowed)

            text = "Доступ отозван"

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            json={
                "callback_query_id": update["callback_query"]["id"],
                "text": text
            }
        )

        return "ok"

    # обработка команд
    if "message" in update:

        text = update["message"].get("text", "")

        if text == "/users":

            allowed = load_allowed()

            if not allowed:
                send_message("Нет разрешённых устройств")
                return "ok"

            for device, name in allowed.items():

                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "Отозвать доступ",
                                "callback_data": f"remove:{device}"
                            }
                        ]
                    ]
                }

                send_message(
                    f"{name}\n{device}",
                    keyboard
                )

    return "ok"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
