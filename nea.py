import time
import threading
import requests
import dash
from dash import dcc, html
import plotly.graph_objs as go
from collections import deque

# API Endpoints
API_ENDPOINTS = {
    "Temperature": "/v1/environment/air-temperature",
    "Rainfall": "/v1/environment/rainfall",
    "Humidity": "/v1/environment/relative-humidity",
    "Wind Direction": "/v1/environment/wind-direction",
    "Wind Speed": "/v1/environment/wind-speed",
}

# Data storage for charts
history = {key: deque(maxlen=10) for key in API_ENDPOINTS}
timestamps = deque(maxlen=10)

def fetch_api_data():
    while True:
        try:
            timestamp = time.strftime('%H:%M:%S')
            timestamps.append(timestamp)
            for key, endpoint in API_ENDPOINTS.items():
                response = requests.get(f"https://api.data.gov.sg{endpoint}")
                json_data = response.json()
                value = json_data.get("items", [{}])[0].get("readings", [{}])[0].get("value", "N/A")
                history[key].append(value if isinstance(value, (int, float)) else None)
            time.sleep(300)  # Fetch new data every 5 minutes
        except Exception as e:
            print(f"Error fetching data: {e}")
            time.sleep(60)

# Start data fetching in a separate thread
threading.Thread(target=fetch_api_data, daemon=True).start()

# Dash App Setup
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Weather Dashboard", style={'textAlign': 'center'}),
    dcc.Tabs(id='tabs', value='Temperature', children=[
        dcc.Tab(label=key, value=key) for key in API_ENDPOINTS
    ]),
    html.Div(id='data-display'),
    dcc.Graph(id='trend-chart')
])

@app.callback(
    [dash.Output('data-display', 'children'), dash.Output('trend-chart', 'figure')],
    [dash.Input('tabs', 'value')]
)
def update_dashboard(selected_param):
    current_value = history[selected_param][-1] if history[selected_param] else 'N/A'
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=list(timestamps), y=list(history[selected_param]),
                                mode='lines+markers', name=selected_param))
    figure.update_layout(title=f"{selected_param} Trend", xaxis_title='Time', yaxis_title=selected_param)
    return f"Current {selected_param}: {current_value}", figure

if __name__ == '__main__':
    app.run_server(debug=True)
