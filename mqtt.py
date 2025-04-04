import paho.mqtt.client as mqtt
import json
import re
import threading
import time

# MQTT Configuration
BROKER = "460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "deva33369"
PASSWORD = "Dinesh0507"

# Topics
TOPIC_RECEIVE = "sensor"  # Receiving from LoRa
TOPIC_PUBLISH = "sensor"  # Sending to Node-RED

# Buffer to store fragmented messages
message_buffer = ""

# Global flag to indicate when to send data to Node-RED
send_data_flag = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_RECEIVE)
    else:
        print(f"❌ Connection failed (code: {rc})")

def on_message(client, userdata, msg):
    global message_buffer
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

        # 💡 FIX: Remove extra `}` if detected
        if message_buffer[end+1:end+2] == "}":
            message_buffer = message_buffer[:end+1] + message_buffer[end+2:]

        try:
            # Remove checksum if present
            json_str = re.sub(r',\s*"checksum":\d+\s*}$', '}', json_str)

            # Ensure JSON does not have unexpected spaces
            json_str = re.sub(r'\s+', '', json_str)

            # Parse JSON
            data = json.loads(json_str)

            # Format and publish
            formatted_data = {
                "nodeID": data.get("nodeID"),
                "destinationID": data.get("destinationID"),
                "eCO2": data.get("eCO2"),
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "mosquito": data.get("mosquito") if data.get("mosquito") is not None else None,  # Handle undefined mosquito count
                "location": data.get("location"),
                "timestamp": data.get("timestamp") or None
            }

            print("📥 Received:", formatted_data)

            # Set the flag to send data to Node-RED every 15 seconds
            global send_data_flag
            send_data_flag = True

            # Remove processed message from buffer
            message_buffer = message_buffer[end+1:].strip()

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Skipping malformed JSON: {json_str} (Error: {e})")
            message_buffer = message_buffer[end+1:].strip()

def send_data_to_nodered(client):
    global send_data_flag
    while True:
        if send_data_flag:
            # Send the data to Node-RED
            formatted_data = {
                "nodeID": 2,  # Dummy data
                "destinationID": "821446",
                "eCO2": 428,
                "temperature": 25.0,
                "humidity": 79.0,
                "mosquito": 0,
                "location": "level 2",
                "timestamp": None  # Replace with actual timestamp if needed
            }
            print(f"🚀 Published to Node-RED: {formatted_data}")
            client.publish(TOPIC_PUBLISH, json.dumps(formatted_data))
            send_data_flag = False  # Reset the flag after sending data

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
