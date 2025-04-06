

#include <SPI.h>
#include <RH_RF95.h>
#include <SoftwareSerial.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2
#define RF95_FREQ 889.0

SoftwareSerial piSerial(8, 9); // RX, TX

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for serial port
  
  Serial.println("Starting Central Node");
  
  piSerial.begin(9600);

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  if (!rf95.init()) {
    Serial.println("LoRa init failed!");
    while (1);
  }
  
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  
  // Settings for reliable communication
  rf95.setTxPower(13, false);
  rf95.setModemConfig(RH_RF95::Bw125Cr45Sf128); // Medium range, reliable
  rf95.setPayloadCRC(true); // Enable CRC checking
  
  Serial.println("Central node ready");
}

void loop() {
  if (rf95.available()) {
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    
    if (rf95.recv(buf, &len)) {
      // Ensure we have at least 2 bytes (destination + sender)
      if (len >= 2) {
        uint8_t destination = buf[0];
        uint8_t sender = buf[1];
        
        char payload[RH_RF95_MAX_MESSAGE_LEN-1];
        uint8_t payload_len = len - 2;
        memcpy(payload, buf+2, payload_len);
        payload[payload_len] = '\0'; // Null terminate
        
        Serial.print("Received from node ");
        Serial.print(sender);
        Serial.print(": ");
        Serial.println(payload);
        
        // Forward to Raspberry Pi if message is complete
        if (strlen(payload) > 5) { // Basic length check
          piSerial.println(payload);
        }
      }
    }
  }
}