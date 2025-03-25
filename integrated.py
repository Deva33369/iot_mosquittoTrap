import time
import threading
import json
import random  # For simulated data

import dash
from dash import dcc, html, Input, Output
import dash_leaflet as dl
import paho.mqtt.client as mqtt

# Data storage for display
map_data = []

# Map endpoints to tab labels
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

# MQTT Client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_TEMP)
        client.subscribe(TOPIC_HUMIDITY)
        client.subscribe(TOPIC_RAIN)
    else:
        print(f"⚠️ Failed to connect, error code: {rc}")

def on_disconnect(client, userdata, rc):
    print("❌ Disconnected from MQTT Broker")

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

def update_station_data(label, value):
    station_id = "S123"  # Example Station ID; adjust logic for real IDs
    existing_station = next((s for s in map_data if s["station_id"] == station_id), None)
    if existing_station:
        existing_station[label] = value
    else:
        map_data.append({
            "station_id": station_id,
            "station_name": "Example Station",
            "latitude": 1.3521,  # Example latitude
            "longitude": 103.8198,  # Example longitude
            label: value
        })

# Assign MQTT callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Connect and start the MQTT loop
client.connect(BROKER, PORT, 60)
threading.Thread(target=client.loop_forever, daemon=True).start()

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
    dcc.Interval(id="interval-component", interval=5000, n_intervals=0)  # Refresh every 5s
])

@app.callback(
    Output("layer", "children"),
    [Input("interval-component", "n_intervals"),
     Input("search-station-id", "value")]
)
def update_map(n_intervals, search_station_id):
    if not map_data:
        return []  # Return empty if no data available

    # Filter stations by search
    filtered_data = [
        entry for entry in map_data if not search_station_id or
        entry["station_id"].lower() == search_station_id.lower()
    ]

    # Create map markers
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
    app.run_server(debug=True)