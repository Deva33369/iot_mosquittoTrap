import time
import threading
import http.client
import json
import dash
from dash import dcc, html, Input, Output
import dash_leaflet as dl
import paho.mqtt.client as mqtt
import socket  # For network error handling

# Data storage for display
map_data = []

# API Endpoints
API_ENDPOINTS = {
    "Temperature": "/v1/environment/air-temperature",
    "Rainfall": "/v1/environment/rainfall",
    "Humidity": "/v1/environment/relative-humidity"
}

# MQTT Broker and Topics
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "deva33369"
PASSWORD = "Dinesh0507"
TOPIC_TEMP = "mosquito/trap/temperature"
TOPIC_HUMIDITY = "mosquito/trap/humidity"
TOPIC_RAIN = "mosquito/trap/rain"

# Function to fetch API data
def fetch_api_data():
    while True:
        try:
            for label, endpoint in API_ENDPOINTS.items():
                conn = http.client.HTTPSConnection("api.data.gov.sg", timeout=5)  # Timeout added
                conn.request("GET", endpoint)
                res = conn.getresponse()
                response_data = res.read()

                # Parse JSON response
                json_data = json.loads(response_data.decode("utf-8"))
                readings = json_data.get("items", [{}])[0].get("readings", [])
                stations = json_data.get("metadata", {}).get("stations", [])

                # Map readings to stations
                for reading in readings:
                    station_id = reading.get("station_id")
                    value = reading.get("value", "N/A")

                    # Match station metadata
                    station_info = next((s for s in stations if s["id"] == station_id), None)
                    if not station_info:
                        continue

                    latitude = station_info.get("location", {}).get("latitude")
                    longitude = station_info.get("location", {}).get("longitude")
                    name = station_info.get("name", "Unknown")

                    # Check if the station already exists in map_data
                    existing_station = next((s for s in map_data if s["station_id"] == station_id), None)
                    if existing_station:
                        if value != "N/A":
                            existing_station[label] = value
                    else:
                        map_data.append({
                            "station_id": station_id,
                            "station_name": name,
                            "latitude": latitude,
                            "longitude": longitude,
                            label: value
                        })
            time.sleep(300)  # Fetch every 5 minutes
        except (socket.gaierror, http.client.HTTPException) as e:
            print(f"⚠️ Network error fetching API data: {e}")
            time.sleep(60)  # Retry after 1 minute

# Function to handle MQTT messages
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        if msg.topic == TOPIC_TEMP:
            update_station_data("Temperature", payload.get("temperature", "N/A"))
        elif msg.topic == TOPIC_HUMIDITY:
            update_station_data("Humidity", payload.get("humidity", "N/A"))
        elif msg.topic == TOPIC_RAIN:
            update_station_data("Rainfall", payload.get("rain", "N/A"))
    except Exception as e:
        print(f"⚠️ Error processing MQTT message: {e}")

# Update station data dynamically
def update_station_data(label, value):
    station_id = "S123"  # Replace with real mapping logic for MQTT data
    existing_station = next((s for s in map_data if s["station_id"] == station_id), None)
    if existing_station:
        existing_station[label] = value
    else:
        map_data.append({
            "station_id": station_id,
            "station_name": "MQTT Station",
            "latitude": 1.3521,  # Example latitude
            "longitude": 103.8198,  # Example longitude
            label: value
        })

# Start API fetching in a thread
threading.Thread(target=fetch_api_data, daemon=True).start()

# ✅ FIX: Removed `callback_api_version=2` to prevent MQTT error
client = mqtt.Client()  
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.on_message = on_message

# MQTT Connection Callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_TEMP)
        client.subscribe(TOPIC_HUMIDITY)
        client.subscribe(TOPIC_RAIN)
    else:
        print(f"⚠️ Connection failed: {rc}")

client.on_connect = on_connect

try:
    client.connect(BROKER, PORT, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()
except socket.gaierror:
    print("❌ MQTT Connection failed: No internet or DNS issue.")

# Dash App Setup
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Weather Map Dashboard", style={'textAlign': 'center'}),
    dcc.Input(
        id="search-station-id",
        type="text",
        placeholder="Search by Station ID (Eg. S123)",
        debounce=True,
        style={'margin-bottom': '20px', 'width': '300px'}
    ),
    dl.Map(center=[1.3521, 103.8198], zoom=12, children=[
        dl.TileLayer(),
        dl.LayerGroup(id="layer")
    ], style={'width': '100%', 'height': '500px'}),
    dcc.Interval(id="interval-component", interval=5000, n_intervals=0)  # Update every 5 seconds
])

@app.callback(
    Output("layer", "children"),
    [Input("interval-component", "n_intervals"),
     Input("search-station-id", "value")]
)
def update_map(n_intervals, search_station_id):
    if not map_data:
        return []  # Return an empty layer if no data is available

    # Filter stations based on search input
    filtered_data = [
        entry for entry in map_data if not search_station_id or
        entry["station_id"].lower() == search_station_id.lower()
    ]

    # Create markers for the map
    markers = []
    for entry in filtered_data:
        popup_content = html.Div([
            html.B("Station Name: "), html.Span(entry['station_name']), html.Br(),
            html.B("Station ID: "), html.Span(entry['station_id']), html.Br(),
            html.B("Temperature: "), html.Span(f"{entry.get('Temperature', 'N/A')} °C"), html.Br(),
            html.B("Rainfall: "), html.Span(f"{entry.get('Rainfall', 'N/A')} mm"), html.Br(),
            html.B("Humidity: "), html.Span(f"{entry.get('Humidity', 'N/A')} %")
        ])
        marker = dl.Marker(
            position=[entry["latitude"], entry["longitude"]],
            children=dl.Popup(popup_content)
        )
        markers.append(marker)
    return markers

if __name__ == "__main__":
    app.run(debug=True)
