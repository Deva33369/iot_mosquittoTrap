#include <Wire.h>
#include <Adafruit_SGP30.h>
#include <DHT.h>
#include <SPI.h>
#include <RH_RF95.h>
#include <SoftwareSerial.h>

// Pin definitions
#define DHTPIN A0
#define DHTTYPE DHT11
#define MM_OUT_PIN 8        // Target status output pin
#define MM_RX_PIN 9         // Connect to sensor's TX pin
#define MM_TX_PIN 10        // Connect to sensor's RX pin
#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2
#define RF95_FREQ 889.0

Adafruit_SGP30 sgp;
DHT dht(DHTPIN, DHTTYPE);
RH_RF95 rf95(RFM95_CS, RFM95_INT);
SoftwareSerial mmWaveSerial(MM_RX_PIN, MM_TX_PIN);

// Radar data structure
struct RadarData {
  byte targetState;
  int movingDistance;
  byte movingEnergy;
  int stationaryDistance;
  byte stationaryEnergy;
  int detectionDistance;
};

// Variables
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 15000; // 15 seconds
int mosquito = 0;
bool lastDetectionState = false;
byte dataBuffer[64];
int bufferIndex = 0;
RadarData radarData = {0}; // Initialize all values to 0

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for serial port
  
  Wire.begin();
  mmWaveSerial.begin(256000); // LD2410 default baud rate
  pinMode(MM_OUT_PIN, INPUT);
  dht.begin();

  // Initialize LoRa radio
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

}

void loop() {
  // Read mmWave sensor data
  readMMWaveData();
  
  // Check OUT pin for mosquito presence
  bool currentDetection = digitalRead(MM_OUT_PIN);
  if (currentDetection && !lastDetectionState) {
    mosquito++;
  }
  lastDetectionState = currentDetection;

  // Send data at regular intervals
  if (millis() - lastSendTime >= sendInterval) {
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
    json += "\"destinationID\":\"821446\",";
    json += "\"eCO2\":" + String(sgp.eCO2) + ",";
    json += "\"temperature\":" + String(temp, 1) + ",";
    json += "\"humidity\":" + String(hum, 1) + ",";
    json += "\"mosquito\":" + String(mosquito) + ",";
    json += "\"location\":\"level 2\"}";
    
    // Print JSON to Serial
    Serial.println(json);
    
    // Send via LoRa
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    json.getBytes(buf, RH_RF95_MAX_MESSAGE_LEN);
    rf95.send(buf, strlen((char*)buf));
    rf95.waitPacketSent();
    
    lastSendTime = millis();
  }
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