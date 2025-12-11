from flask import Flask, request, jsonify

app = Flask(__name__)

# API-nøgle 
API_KEY = "hemmelig_nokkel123" # Skal være den sammen som på Esp32

# Globale variabler fra ESP32
value_part = None
time_part = None

# Hvad vi sender til ESP32 
id_send = 1
Pille = 1
time_log = [(7, 0), (13, 00), (18, 00)]

def check_api_key(req):
    key = req.headers.get("x-api-key")
    return key == API_KEY

# RFID-liste
# mangler at find de rigte tal 
rfid_list = [
    143,
    234,
    5543,
]


@app.route("/send", methods=["POST"])
def receive_data():
    global value_part, time_part

    if not check_api_key(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if 'RF_log_time' not in data:
        return jsonify({"error": "RF_log_time missing"}), 400

    rf0 = data['RF_log_time']
    value_part, time_part = rf0

    print("Data modtaget fra ESP32:", data)
    print("RF0 værdi:", value_part)
    print("RF0 tid:", time_part)

    if value_part in rfid_list:
        plads = rfid_list.index(value_part) + 1
        print(f"RFID fundet! Plads: {plads}")
    else:
        print("RFID IKKE fundet!")

    response_data = {
        "id": id_send,
        "Give": Pille,
        "Tider": time_log,
    }

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
