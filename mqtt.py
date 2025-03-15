import paho.mqtt.client as mqtt
import json
import time
import random  # Simulating sensor data changes

# HiveMQ Cloud credentials
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883  # Secure MQTT port
USERNAME = "deva33369"
PASSWORD = "Dinesh0507"

# MQTT Topics
TOPIC_TEMP = "mosquito/trap/temperature"
TOPIC_HUMIDITY = "mosquito/trap/humidity"
TOPIC_CO2 = "mosquito/trap/co2"
TOPIC_RAIN = "mosquito/trap/rain"

# MQTT Client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()  # Enable TLS

# Callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud MQTT Broker!")
    else:
        print(f"⚠️ Connection failed with error code {rc}")

def on_disconnect(client, userdata, rc):
    print("❌ Disconnected from MQTT Broker")

# Assign callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Connect to the broker
client.connect(BROKER, PORT, 60)

# Start the MQTT loop in a separate thread
client.loop_start()

try:
    while True:
        # Simulated sensor data with slight variations
        sensor_data = {
            "temperature": round(random.uniform(28.0, 30.0), 2),
            "humidity": random.randint(80, 90),
            "co2": random.randint(350, 450),
            "rain": random.choice(["Yes", "No"])
        }

        # Publish each sensor value
        client.publish(TOPIC_TEMP, json.dumps({"temperature": sensor_data["temperature"]}))
        client.publish(TOPIC_HUMIDITY, json.dumps({"humidity": sensor_data["humidity"]}))
        client.publish(TOPIC_CO2, json.dumps({"co2": sensor_data["co2"]}))
        client.publish(TOPIC_RAIN, json.dumps({"rain": sensor_data["rain"]}))

        print(f"📡 Data sent: {sensor_data}")

        # Send data every 5 seconds
        time.sleep(5)

except KeyboardInterrupt:
    print("\n🛑 Stopping publisher...")

finally:
    client.loop_stop()
    client.disconnect()
    print("🔌 MQTT Client Disconnected")