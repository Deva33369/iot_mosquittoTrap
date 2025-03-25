import paho.mqtt.client as mqtt
import json

# HiveMQ Cloud credentials
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883  # Secure MQTT port
USERNAME = "deva33369"
PASSWORD = "Dinesh0507"

# MQTT Topic
TOPIC = "sensor"

# MQTT Client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()  # Enable TLS

# Callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud MQTT Broker!")
        client.subscribe(TOPIC)  # Subscribe to the topic
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"⚠️ Connection failed with error code {rc}")

def on_disconnect(client, userdata, rc):
    print("❌ Disconnected from MQTT Broker")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())  # Decode and parse JSON
        print(f"📥 Received data: {payload}")
    except json.JSONDecodeError:
        print(f"⚠️ Received malformed message: {msg.payload.decode()}")

# Assign callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER, PORT, 60)

# Start the MQTT loop to listen for messages
client.loop_forever()
