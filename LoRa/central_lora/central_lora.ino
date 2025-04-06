#include <SPI.h>
#include <RH_RF95.h>
#include <SoftwareSerial.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2
#define RF95_FREQ 889.0

// SoftwareSerial to Pi
SoftwareSerial piSerial(8, 9); // RX, TX

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  Serial.begin(9600);      // For USB Serial Monitor
  piSerial.begin(9600);    // For Pi connection
  delay(1000);

  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, LOW); delay(10);
  digitalWrite(RFM95_RST, HIGH); delay(10);

  if (!rf95.init()) {
    Serial.println("LoRa init failed");
    while (1);
  }

  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("Frequency set failed");
    while (1);
  }

  rf95.setTxPower(13, false);
  Serial.println("LoRa RX Ready");
}

void loop() {
  if (rf95.available()) {
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf95.recv(buf, &len)) {
      buf[len] = '\0';  // Null-terminate
      String json = String((char*)buf);

      // Print to Serial Monitor
      Serial.println("Received JSON:");
      Serial.println(json);

      // Send to Raspberry Pi via TX
      piSerial.println(json);
      piSerial.flush(); // Ensure all bytes sent
    } else {
      Serial.println("Receive failed");
    }
  }
}
