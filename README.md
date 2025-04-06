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

## Raspberry Pi MQTT Central Node

### File: `central_node_pi.c`
This file is the MQTT client running on the Raspberry Pi. It receives data via serial from the central LoRa or LoRaMesh node and publishes it to an MQTT broker.

### Compile & Run

```bash
gcc -o central_node_pi central_node_pi.c -lpaho-mqtt3cs
./central_node_pi
