#include <ArduinoJson.h>

// Constants
const int BAUD_RATE = 9600;
int counter = 0;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  // initialize serial
  Serial.begin(BAUD_RATE);
  while (!Serial) {
    // Wait for serial to establish
  }
  Serial.println("{ \"status\":\"Online\"");
}


void sendTestJSON() {
    String s = "{";
    s += "\"test\":" + String(int(counter));
    s += "}";
    counter++;
    Serial.println(s);
}


void readJSON(String str) {
  char json[50];
  str.toCharArray(json, 50);
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.parseObject(json);
  double action = root["action"];
  if (action==1) {
    digitalWrite(LED_BUILTIN, HIGH);  
  } else if (action==2) {
    digitalWrite(LED_BUILTIN, LOW);  
  }
}

void loop() {  
  sendTestJSON();
  while (Serial.available() > 0) {
    readJSON(Serial.readString());
  }
  delay(500);
}









