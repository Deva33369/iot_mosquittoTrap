#include <Wire.h>
#include <Adafruit_SGP30.h>
#include <DHT.h>
#include <SPI.h>
#include <RH_RF95.h>
#include <SoftwareSerial.h>

// Pin definitions
#define DHTPIN A0
#define DHTTYPE DHT11
#define MM_OUT_PIN 8
#define MM_RX_PIN 9
#define MM_TX_PIN 10
#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2
#define RF95_FREQ 889.0

// Mesh configuration
#define BROADCAST_ADDRESS 255
#define MAX_HOPS 5
#define ACK_TIMEOUT 3000
#define ROUTE_UPDATE_INTERVAL 30000

Adafruit_SGP30 sgp;
DHT dht(DHTPIN, DHTTYPE);
RH_RF95 rf95(RFM95_CS, RFM95_INT);
SoftwareSerial mmWaveSerial(MM_RX_PIN, MM_TX_PIN);

// Mesh network variables
uint8_t nodeID = 2;            // Change per node
uint8_t centralNodeID = 1;     //Change per building (Central NodeID)
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 5000;
unsigned long lastRouteUpdateTime = 0;

// Message header (includes destination in first byte)
struct MeshMessage {
  uint8_t destination;    // First byte indicates destination
  uint8_t sender;
  uint8_t originalSender;
  uint8_t messageID;
  uint8_t hopCount;
  uint8_t maxHops;
  uint8_t type;
  // Followed by payload
};

// Sensor data
struct RadarData {
  byte targetState;
  int movingDistance;
  byte movingEnergy;
  int stationaryDistance;
  byte stationaryEnergy;
  int detectionDistance;
};

// Variables
int mosquito = 0;
bool lastDetectionState = false;
byte dataBuffer[64];
int bufferIndex = 0;
RadarData radarData = {0};

void setup() {
  Serial.begin(9600);
  Wire.begin();
  pinMode(MM_OUT_PIN, INPUT);
  dht.begin();

  // Initialize LoRa
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, LOW); 
  delay(10);
  digitalWrite(RFM95_RST, HIGH); 
  delay(10);

  if (!rf95.init()) {
    Serial.println(F("{\"error\":\"LoRa init failed\"}"));
    while (1);
  }
  rf95.setFrequency(RF95_FREQ);
  rf95.setTxPower(13, false);
  
  // Initialize SGP30
  if (!sgp.begin()) {
    Serial.println(F("{\"error\":\"SGP30 not found\"}"));
    while (1);
  }

  Serial.println("LoRa mesh node " + String(nodeID) + " initialized");
}

void loop() {
  // Read mmWave sensor data
  readMMWaveData();
  checkMosquitoSensor();

  // Handle incoming messages
  if (rf95.available()) {
    handleIncomingMessage();
  }

  // Send sensor data periodically
  if (millis() - lastSendTime >= sendInterval) {
    sendSensorData();
    lastSendTime = millis();
  }
}

// Check OUT pin for mosquito presence
void checkMosquitoSensor() {
  bool currentDetection = digitalRead(MM_OUT_PIN);
  if (currentDetection && !lastDetectionState) {
    mosquito++;
  }
  lastDetectionState = currentDetection;
}

void readMMWaveData() {
  while (mmWaveSerial.available()) {
    byte incomingByte = mmWaveSerial.read();
    
    // Frame parsing logic
    if (bufferIndex == 0 && incomingByte == 0xF4) {
      dataBuffer[bufferIndex++] = incomingByte;
    } 
    else if (bufferIndex == 1 && incomingByte == 0xF3) {
      dataBuffer[bufferIndex++] = incomingByte;
    }
    else if (bufferIndex == 2 && incomingByte == 0xF2) {
      dataBuffer[bufferIndex++] = incomingByte;
    }
    else if (bufferIndex == 3 && incomingByte == 0xF1) {
      dataBuffer[bufferIndex++] = incomingByte;
    }
    else if (bufferIndex >= 4) {
      dataBuffer[bufferIndex++] = incomingByte;
      
      if (bufferIndex >= 13) {
        // Check for frame end
        if (dataBuffer[bufferIndex-4] == 0xF8 && 
            dataBuffer[bufferIndex-3] == 0xF7 && 
            dataBuffer[bufferIndex-2] == 0xF6 && 
            dataBuffer[bufferIndex-1] == 0xF5) {
          
          parseDataFrame();
          bufferIndex = 0;
        }
        
        if (bufferIndex >= sizeof(dataBuffer)) {
          bufferIndex = 0;
        }
      }
    }
    else {
      bufferIndex = 0;
    }
  }
}

void parseDataFrame() {
  if (dataBuffer[4] == 0x02) { // Basic info frame
    radarData.targetState = dataBuffer[6];
    radarData.movingDistance = dataBuffer[7] | (dataBuffer[8] << 8);
    radarData.movingEnergy = dataBuffer[9];
    radarData.stationaryDistance = dataBuffer[10] | (dataBuffer[11] << 8);
    radarData.stationaryEnergy = dataBuffer[12];
    radarData.detectionDistance = dataBuffer[13] | (dataBuffer[14] << 8);
    
    // Debug print if needed
    /*
    Serial.print(F("{\"radar_update\":{\"moving\":"));
    Serial.print(radarData.movingDistance);
    Serial.print(F(",\"stationary\":"));
    Serial.print(radarData.stationaryDistance);
    Serial.println(F("}}"));
    */
  }
}

// Mesh networking functions
void sendSensorData() {
  // Read environmental sensors
  if (!sgp.IAQmeasure()) {
    Serial.println(F("{\"error\":\"Failed to read SGP30\"}"));
    delay(1000);
    return;
  }
  
  // Read DHT with retry logic
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  if (isnan(temp) || isnan(hum)) {
    delay(2000);  // Wait before retry
    temp = dht.readTemperature();
    hum = dht.readHumidity();
    
    if (isnan(temp) || isnan(hum)) {
      Serial.println(F("{\"error\":\"Failed to read DHT11\"}"));
      return;
    }
  }

  // Create JSON payload
  String json = "{";
  json += "\"nodeID\":" + String(nodeID) + ",";
  json += "\"destinationID\":\"821446\",";
  json += "\"eCO2\":" + String(sgp.eCO2) + ",";
  json += "\"temperature\":" + String(temp, 1) + ",";
  json += "\"humidity\":" + String(hum, 1) + ",";
  json += "\"mosquito\":" + String(mosquito) + ",";
  json += "\"location\":\"level 2\"}";

  // Calculate checksum
  uint8_t checksum = 0;
  for (size_t i = 0; i < json.length(); i++) {
    checksum ^= json.charAt(i);
  }
  json += ",\"checksum\":" + String(checksum) + "}";

  // Prepare message buffer
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  
  // Message header (first 2 bytes)
  buf[0] = centralNodeID;  // Destination
  buf[1] = nodeID;         // Sender

  // Copy JSON payload after header
  uint8_t payloadLength = json.length();
  if (payloadLength > RH_RF95_MAX_MESSAGE_LEN - 2) {
    Serial.println(F("{\"error\":\"Message too long\"}"));
    return;
  }
  json.getBytes(buf + 2, RH_RF95_MAX_MESSAGE_LEN - 2);

  //Print JSON to Serial
  Serial.print("Sending: ");
  Serial.println(json);
  Serial.print("Message length: ");
  Serial.println(2 + payloadLength);

  // Send message
  if (!rf95.send(buf, 2 + payloadLength)) {
    Serial.println(F("{\"error\":\"Send failed\"}"));
  }
  rf95.waitPacketSent();

  Serial.println(F("{\"status\":\"Message sent\"}"));
}

void handleIncomingMessage() {
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
  
  if (rf95.recv(buf, &len)) {
    MeshMessage* header = (MeshMessage*)buf;
    String payload = String((char*)(buf + sizeof(MeshMessage)));
    
    // Process message based on destination
    if(header->destination == nodeID || header->destination == BROADCAST_ADDRESS) {
      processMessage(header, payload);
    }
    
    // Forward if needed
    if(header->destination != nodeID && 
       header->hopCount < header->maxHops &&
       header->destination != BROADCAST_ADDRESS) {
      forwardMessage(header, payload);
    }
  }
}

void processMessage(MeshMessage* header, String payload) {
  Serial.print("Received from ");
  Serial.print(header->originalSender);
  Serial.print(" via ");
  Serial.print(header->sender);
  Serial.print(": ");
  Serial.println(payload);
  
  // For data messages intended for us
  if(header->type == 1 && header->destination == nodeID) {
    if(header->originalSender != nodeID) {
      forwardToCentral(header, payload);
    }
  }
}

void forwardMessage(MeshMessage* originalHeader, String payload) {
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  MeshMessage* header = (MeshMessage*)buf;
  
  // Copy original header
  memcpy(header, originalHeader, sizeof(MeshMessage));
  
  // Update header
  header->sender = nodeID;
  header->hopCount++;
  
  // Copy payload
  payload.getBytes(buf + sizeof(MeshMessage), RH_RF95_MAX_MESSAGE_LEN - sizeof(MeshMessage));
  
  // Resend
  rf95.send(buf, sizeof(MeshMessage) + payload.length());
  rf95.waitPacketSent();
  
  Serial.println("Forwarded message to " + String(header->destination));
}

void forwardToCentral(MeshMessage* originalHeader, String payload) {
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  MeshMessage* header = (MeshMessage*)buf;
  
  // Create new header
  header->destination = centralNodeID;
  header->sender = nodeID;
  header->originalSender = originalHeader->originalSender;
  header->messageID = originalHeader->messageID;
  header->hopCount = originalHeader->hopCount + 1;
  header->maxHops = originalHeader->maxHops;
  header->type = originalHeader->type;
  
  // Copy payload
  payload.getBytes(buf + sizeof(MeshMessage), RH_RF95_MAX_MESSAGE_LEN - sizeof(MeshMessage));
  
  // Send
  rf95.send(buf, sizeof(MeshMessage) + payload.length());
  rf95.waitPacketSent();
  
  Serial.println("Forwarded to central node");
}