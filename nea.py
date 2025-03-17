import time
import threading
import http.client
import json
import dash
from dash import dcc, html

# Data storage for display
data = {
    "Temperature": [],
    "Rainfall": [],
    "Humidity": [],
    "Wind Direction": [],
    "Wind Speed": []
}

# Map endpoints to tab labels
API_ENDPOINTS = {
    "Temperature": "/v1/environment/air-temperature",
    "Rainfall": "/v1/environment/rainfall",
    "Humidity": "/v1/environment/relative-humidity",
    "Wind Direction": "/v1/environment/wind-direction",
    "Wind Speed": "/v1/environment/wind-speed"
}

def fetch_api_data():
    while True:
        try:
            for label, endpoint in API_ENDPOINTS.items():
                conn = http.client.HTTPSConnection("api.data.gov.sg")
                conn.request("GET", endpoint)
                res = conn.getresponse()
                response_data = res.read()
                
                json_data = json.loads(response_data.decode("utf-8"))
                readings = json_data.get("items", [{}])[0].get("readings", [])

                # Collect all readings for the given endpoint
                values = [
                    f"Station: {reading.get('station_id', 'Unknown')} | Value: {reading.get('value', 'N/A')}"
                    for reading in readings
                ]
                data[label] = values
            time.sleep(300)  # Fetch new data every 5 minutes
        except Exception as e:
            print(f"⚠️ Error fetching API data: {e}")
            time.sleep(60)  # Retry in 1 minute if an error occurs

# Start API fetching in a separate thread
threading.Thread(target=fetch_api_data, daemon=True).start()

# Dash App Setup
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Weather Dashboard", style={'textAlign': 'center'}),
    dcc.Tabs(id="tabs", value="Temperature", children=[
        dcc.Tab(label=label, value=label) for label in API_ENDPOINTS.keys()
    ]),
    html.Div(id="data-display")
])

@app.callback(
    dash.Output("data-display", "children"),
    [dash.Input("tabs", "value")]
)
def update_dashboard(selected_tab):
    # Display all readings for the selected tab
    readings = data.get(selected_tab, [])
    if not readings:
        return html.Div(f"No data available for {selected_tab}.")
    
    data_display = html.Div([
        html.Ul([html.Li(reading) for reading in readings])
    ])
    return data_display

if __name__ == "__main__":
    app.run_server(debug=True)
