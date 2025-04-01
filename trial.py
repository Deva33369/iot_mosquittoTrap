import json
import random
import threading
import time
import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "mosquito/trap/sensor_data"

client = mqtt.Client()
client.username_pw_set("deva33369", "Dinesh0507")
client.tls_set()

def publish_data():
    while True:
        sensor_data = {
            "nodeID": 2,
            "eCO2": random.randint(400, 2000),
            "temperature": round(random.uniform(20.0, 35.0), 1),
            "humidity": random.randint(40, 90),
            "mosquito": random.randint(0, 50),
            "location": "E2-05-07"  # Your location format
        }
        client.publish(TOPIC, json.dumps(sensor_data))
        print(f"Published: {sensor_data}")
        time.sleep(30)  # 30-second interval

client.connect(BROKER, PORT, 60)
threading.Thread(target=client.loop_forever, daemon=True).start()
threading.Thread(target=publish_data, daemon=True).start()

while True: time.sleep(1)