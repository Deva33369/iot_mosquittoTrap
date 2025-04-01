import time
import threading
import http.client
import json
import paho.mqtt.client as mqtt
import socket  # For network error handling

# MQTT Broker and Topic
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "deva33369"
PASSWORD = "Dinesh0507"
TOPIC_TEMP = "mosquito/trap/temperature"  # Publishing & Subscribing temperature

# API Endpoint for Temperature
API_URL = "/v1/environment/air-temperature"

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()

# Callback when connected to MQTT Broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_TEMP)  # Subscribe to receive messages
        print(f"📡 Subscribed to: {TOPIC_TEMP}")
    else:
        print(f"⚠️ Connection failed: {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        print(f"📥 Received message on {msg.topic}: {payload}")  # Print received data
    except Exception as e:
        print(f"⚠️ Error decoding message: {e}")

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT Broker
try:
    client.connect(BROKER, PORT, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()
except socket.gaierror:
    print("❌ MQTT Connection failed: No internet or DNS issue.")

# Function to Fetch Temperature, Station Name and Publish to MQTT
def fetch_and_publish_temperature():
    while True:
        try:
            print("🌡️ Fetching temperature data from API...")
            conn = http.client.HTTPSConnection("api.data.gov.sg", timeout=5)
            conn.request("GET", API_URL)
            res = conn.getresponse()
            response_data = res.read()

            # Parse JSON response
            json_data = json.loads(response_data.decode("utf-8"))
            readings = json_data.get("items", [{}])[0].get("readings", [])
            stations = json_data.get("metadata", {}).get("stations", [])

            if not readings or not stations:
                print("⚠️ No temperature data available from API.")
            else:
                for reading in readings:
                    station_id = reading.get("station_id", "Unknown")
                    temperature = reading.get("value", "N/A")

                    # Match station ID to get station name
                    station_info = next((s for s in stations if s["id"] == station_id), None)
                    station_name = station_info.get("name", "Unknown") if station_info else "Unknown"

                    # Publish to MQTT
                    temp_payload = json.dumps({
                        "station_id": station_id,
                        "station_name": station_name,
                        "temperature": temperature
                    })
                    client.publish(TOPIC_TEMP, temp_payload)
                    print(f"📡 Published Temperature Data: {temp_payload}")

            time.sleep(300)  # Fetch and publish every 5 minutes

        except (socket.gaierror, http.client.HTTPException, json.JSONDecodeError) as e:
            print(f"⚠️ Network/API Error: {e}")
            time.sleep(60)  # Retry after 1 minute

# Start fetching and publishing temperature in a thread
threading.Thread(target=fetch_and_publish_temperature, daemon=True).start()

# Keep the script running
while True:
    time.sleep(1)
