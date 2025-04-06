# Internet of Things in Mosquito Trapping and Dengue Hotspot Tracking 

## Authors
- Kumar Devadharshini (2301047)
- Ong Yi Qi (2301157)
- Karianne Lai Wei Xuan (2301192)
- Woo Li Ling Hannah (2301170)
- Safiullah Faheema Banu (2303489)

---

## Overview

This project focuses on building an IoT system for intelligent mosquito trapping and tracking of dengue hotspots using LoRa and LoRa Mesh networks. Sensor nodes (placed in traps) collect environmental and mosquito presence data, which are transmitted via LoRa or LoRaMesh to central nodes. These central nodes forward the data to the cloud via MQTT from a Raspberry Pi.

---

## Project Structure

### LoRa (Point-to-Point Communication)
- **central_lora**  
  - To be deployed on the LoRa module connected to the Raspberry Pi.
- **sensor_lora**  
  - To be deployed on the LoRa modules attached to individual mosquito traps.

### LoRaMesh (Multi-Hop Mesh Communication)
- **central_loraMesh**  
  - To be deployed on the LoRa module connected to the Raspberry Pi.
  - Each central node must have a unique `central_node_ID`.
- **sensor_loraMesh**  
  - To be deployed on the LoRa modules connected to mosquito trap sensors.
  - Each sensor node must have:
    - A unique `node_ID`
    - A `central_node_ID` specifying which central node it connects to
    - A `destinationID`, typically the building's postal code

---
## Cloud Data Pipeline
### MQTT Broker (HiveMQ Cloud)
- Secure TLS connection (port 8883)

- Authentication with username/password

- Dedicated topics for sensor data

- High availability cloud infrastructure


### Raspberry Pi MQTT Central Node

## Compile & Run

# Compile the central node program
gcc -o central_node_pi central_node_pi.c -lpaho-mqtt3cs

# Execute the compiled program
./central_node_pi

### File: `central_node_pi.c`
This file is the MQTT client running on the Raspberry Pi. It receives data via serial from the central LoRa or LoRaMesh node and publishes it to an MQTT broker.

### Python MQTT Client (Data Processor)
- Connects to HiveMQ Cloud

- Handles message fragmentation and JSON parsing

- Formats data with timestamps

- Maintains data buffer for incomplete messages

## Data Processing & Storage 
- * ### Node-RED *
- Receives and validates MQTT messages

- Transforms data into consistent schema

- Implements data quality checks

- Routes data to MongoDB

### MongoDB
- Structured document storage

- Time-series data optimization

- Indexed for fast queries

- Secure data persistence

## Visualisation Dashboard 
### Node-RED Dashboard
- Real-time monitoring of sensor data

- Historical trend visualization

- Alerting for threshold violations

- Multi-device responsive design

## Data Flow 
- Sensor nodes collect environmental data (temperature, humidity, eCO2) and mosquito counts

- Data transmits via LoRa/LoRaMesh to Raspberry Pi gateways

- Gateways forward data to HiveMQ Cloud via MQTT

- Python processor formats and validates incoming data

- Node-RED processes and stores data in MongoDB

- Dashboard visualizes current and historical data

### Message Format 
{
  "nodeID": "sensor01",
  "destinationID": "821446",
  "eCO2": 450,
  "temperature": 23.5,
  "humidity": 45.2,
  "mosquito": 12,
  "location": "lab-1",
  "timestamp": "2023-06-15T14:32:45.123Z"
}

## Key Features 
- Real-time Monitoring: Immediate visibility of mosquito trap data

- Mesh Networking: Flexible deployment with LoRaMesh

- Data Integrity: Robust handling of network issues and malformed data

- Secure Pipeline: TLS encryption throughout the system

- Historical Analysis: MongoDB storage enables trend analysis

- Scalable Architecture: Cloud-based components handle growing deployments

## Setup Instructions 
### Field Deployment:

- Configure sensor nodes with unique IDs

- Set up LoRa/LoRaMesh network parameters

- Deploy Raspberry Pi gateways

### Cloud Setup:

- Configure HiveMQ Cloud instance

- Set up MQTT topics and access controls

- Deploy Python data processor

### Node-RED & MongoDB:

- Install and configure Node-RED flows

- Set up MongoDB connection

- Design dashboard interface

## Maintenance & Monitoring
-**The system includes:**

- Connection health checks

- Data flow metrics

- Alerting for system failures

- Comprehensive logging


