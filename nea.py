import time
import threading
import http.client
import json
import dash
from dash import dcc, html, Input, Output
import dash_leaflet as dl

# Data storage for display
map_data = []

# Map endpoints to tab labels
API_ENDPOINTS = {
    "Temperature": "/v1/environment/air-temperature",
    "Rainfall": "/v1/environment/rainfall",
    "Humidity": "/v1/environment/relative-humidity"
}

def fetch_api_data():
    while True:
        try:
            map_data.clear()  # Clear old data
            for label, endpoint in API_ENDPOINTS.items():
                conn = http.client.HTTPSConnection("api.data.gov.sg")
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
                        continue  # Skip if station ID not found

                    latitude = station_info.get("location", {}).get("latitude")
                    longitude = station_info.get("location", {}).get("longitude")
                    name = station_info.get("name", "Unknown")

                    # Check if the station already exists in map_data
                    existing_station = next((s for s in map_data if s["station_id"] == station_id), None)
                    if existing_station:
                        if value != "N/A":  # Only update if the value is valid
                            existing_station[label] = value
                    else:
                        map_data.append({
                            "station_id": station_id,
                            "station_name": name,
                            "latitude": latitude,
                            "longitude": longitude,
                            label: value  # Add the current weather parameter
                        })
            time.sleep(300)  # Fetch new data every 5 minutes
        except Exception as e:
            print(f"⚠️ Error fetching API data: {e}")
            time.sleep(60)  # Retry in 1 minute if an error occurs


# Start API fetching in a separate thread
threading.Thread(target=fetch_api_data, daemon=True).start()

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
    dcc.Interval(id="interval-component", interval=300000, n_intervals=0)
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
    if search_station_id:
        filtered_data = [
            entry for entry in map_data if entry["station_id"].lower() == search_station_id.lower()
        ]
    else:
        filtered_data = map_data

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
    app.run_server(debug=True)
