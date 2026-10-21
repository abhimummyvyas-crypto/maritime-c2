from flask import Flask, render_template, jsonify
import websocket
import json
import threading
import time

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "196b58709cb66abb47a22899fb2e2139ca7e7c04"  # Paste your key inside the quotes
TARGET_MMSI = "636026627" # Replace with your new MMSI

# Global variables to store the live data
live_data = {
    "live_lat": 12.8000,
    "live_lon": 53.1800,
    "server_time": time.strftime("%H:%M:%S")
}

def connect_ais_stream():
    """Runs continuously in the background to catch satellite updates"""
    def on_message(ws, message):
        global live_data
        msg = json.loads(message)
        
        # Check if the message is a Position Report
        if msg.get("MessageType") == "PositionReport":
            report = msg.get("Message", {}).get("PositionReport", {})
            # Check if it is our target ship
            if str(report.get("UserID")) == TARGET_MMSI:
                live_data["live_lat"] = report.get("Latitude")
                live_data["live_lon"] = report.get("Longitude")
                live_data["server_time"] = time.strftime("%H:%M:%S")

    def on_error(ws, error):
        print(f"WebSocket Error: {error}")

    def on_open(ws):
        # Tell AISStream we only want position reports for our specific ship
        subscribe_message = {
            "APIKey": API_KEY,
            "BoundingBoxes": [[[-90, -180], [90, 180]]], # Global bounding box
            "FiltersShipMMSI": [TARGET_MMSI],
            "FilterMessageTypes": ["PositionReport"]
        }
        ws.send(json.dumps(subscribe_message))

    # Keep reconnecting if the satellite feed drops
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.aisstream.io/v0/stream",
                on_message=on_message,
                on_error=on_error,
                on_open=on_open
            )
            ws.run_forever()
        except Exception:
            time.sleep(5) # Wait 5 seconds and try again

# Start the background listener before the server boots up
listener_thread = threading.Thread(target=connect_ais_stream, daemon=True)
listener_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/radar')
def radar_data():
    # Instantly hand the dashboard the freshest coordinates we have
    return jsonify({
        "target": "MV RUEN",
        "live_lat": live_data["live_lat"],
        "live_lon": live_data["live_lon"],
        "server_time": live_data["server_time"]
    })

if __name__ == '__main__':
    app.run(debug=False, port=5000)