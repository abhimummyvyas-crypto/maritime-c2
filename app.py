from flask import Flask, render_template, jsonify
import requests
import time

app = Flask(__name__)

# --- CONFIGURATION ---
# Replace this with a real API key from MarineTraffic, Spire, etc.
API_KEY = "YOUR_FREE_API_KEY_HERE"
# The MMSI (Maritime Mobile Service Identity) of the ship you want to track
# 215860000 is the real MMSI for the MV Ruen
TARGET_MMSI = "215860000" 

# Fallback coordinates in case the real-world API is offline or rate-limits you
last_known_lat = 12.8000
last_known_lon = 53.1800

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/radar')
def radar_data():
    global last_known_lat, last_known_lon
    
    # Example API endpoint (format matches standard maritime data providers)
    api_url = f"https://api.marinetraffic.com/api/exportvessel/v:8/{API_KEY}/mmsi:{TARGET_MMSI}/protocol:json"
    
    try:
        # Ask the real-world satellite API for the ship's data
        # timeout=3 ensures your dashboard doesn't freeze if the API is slow
        response = requests.get(api_url, timeout=3)
        
        # If the API accepts our key and sends data back (Status 200)
        if response.status_code == 200:
            data = response.json()
            
            # Extract the actual latitude and longitude from the provider's JSON
            # (Note: Exact dictionary keys like 'LAT' depend on which API provider you choose)
            last_known_lat = float(data[0]['LAT'])
            last_known_lon = float(data[0]['LON'])
            
    except Exception as e:
        # If the API fails, we silently catch the error and just send the last known location
        pass
        
    return jsonify({
        "target": "MV RUEN",
        "live_lat": last_known_lat,
        "live_lon": last_known_lon,
        "server_time": time.strftime("%H:%M:%S")
    })

if __name__ == '__main__':
    # In production, Render ignores this block and uses Gunicorn instead.
    app.run(debug=False, port=5000)