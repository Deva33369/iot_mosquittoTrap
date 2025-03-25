import paho.mqtt.client as mqtt
import json

# HiveMQ Cloud credentials (Same as the server)
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883  # Secure MQTT port
USERNAME = "deva33369"
PASSWORD = "Dinesh0507"

# MQTT Topic (Same as the server)
TOPIC = "sensor"

# Callback when connected to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud MQTT Broker!")
        client.subscribe(TOPIC)  # Subscribe to the topic
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"⚠️ Connection failed with error code {rc}")

# Callback when disconnected
def on_disconnect(client, userdata, rc):
    print("❌ Disconnected from MQTT Broker")

# Callback when a message is received
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        json_data = json.loads(payload)  # Decode JSON
        print(f"📥 Received data from server: {json_data}")  # Print the data
    except json.JSONDecodeError:
        print(f"⚠️ Malformed message received: {payload}")

# Debugging logs (optional)
def on_log(client, userdata, level, buf):
    print(f"[LOG] {buf}")

# Create MQTT Client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()  # Enable TLS encryption

# Assign callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_log = on_log  # Uncomment to debug connection issues

# Connect to the broker
print("🔄 Connecting to MQTT Broker...")
client.connect(BROKER, PORT, 60)

# Start the MQTT loop to listen for messages
client.loop_forever()
