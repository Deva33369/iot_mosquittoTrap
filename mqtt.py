import paho.mqtt.client as mqtt
import json
import re
import threading
import time
from datetime import datetime

# MQTT Configuration
BROKER = "303e2aaaa7cf4df1951cfe02e9e5b48e.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "hivemq.webclient.1743741055572"
PASSWORD = "59N1.,BKlPLun?@t0qaX"

# Topics
TOPIC_RECEIVE = "sensor"  # Receiving from LoRa
TOPIC_PUBLISH = "sensor"  # Sending to Node-RED

# Buffer to store fragmented messages
message_buffer = ""
# Store the last received valid data
last_valid_data = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_RECEIVE)
    else:
        print(f"❌ Connection failed (code: {rc})")

def on_message(client, userdata, msg):
    global message_buffer, last_valid_data
    payload = msg.payload.decode().strip()
    
    # Append new data to buffer
    message_buffer += payload

    while True:
        start = message_buffer.find('{')
        end = message_buffer.find('}', start)

        if start == -1 or end == -1:
            # Incomplete JSON, wait for more data
            break

        json_str = message_buffer[start:end+1]

        # Remove extra `}` if detected
        if message_buffer[end+1:end+2] == "}":
            message_buffer = message_buffer[:end+1] + message_buffer[end+2:]

        try:
            # Remove checksum if present
            json_str = re.sub(r',\s*"checksum":\d+\s*}$', '}', json_str)

            # Parse JSON
            data = json.loads(json_str)

            # Format the data with timestamp
            formatted_data = {
                "nodeID": data.get("nodeID"),
                "destinationID": data.get("destinationID", "821446"),
                "eCO2": data.get("eCO2"),
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "mosquito": data.get("mosquito", 0),
                "location": data.get("location", "unknown"),
                "timestamp": datetime.now().isoformat()
            }

            print("📥 Received:", formatted_data)
            
            # Store the valid data
            last_valid_data = formatted_data
            
            # Remove processed message from buffer
            message_buffer = message_buffer[end+1:].strip()

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Skipping malformed JSON: {json_str} (Error: {e})")
            message_buffer = message_buffer[end+1:].strip()

def send_data_to_nodered(client):
    global last_valid_data
    while True:
        if last_valid_data:
            # Send the actual received data to Node-RED
            print(f"🚀 Publishing to Node-RED: {last_valid_data}")
            client.publish(TOPIC_PUBLISH, json.dumps(last_valid_data))
        
        time.sleep(15)  # Wait for 15 seconds before sending data again

# Initialize MQTT client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()  # Enable TLS
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Connecting to MQTT Broker...")
client.connect(BROKER, PORT, 60)

# Start a new thread to send data every 15 seconds
thread = threading.Thread(target=send_data_to_nodered, args=(client,))
thread.daemon = True  # Ensure the thread stops when the main program exits
thread.start()

# Keep the MQTT loop running
client.loop_forever()