#include <ArduinoJson.h>

// Sensor pins
const int buttonPin = 2;
int buttonState = 0;  

// Constants
const int   BAUD_RATE     = 9600;     // Serial comms rate

void setup() {
  // initialize serial
  Serial.begin(BAUD_RATE);
  while (!Serial) {
    // Wait for serial to establish
  }
  Serial.println("{ \"status\":\"Online\"");
   
  // Trigger pins
  pinMode(buttonPin, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
}

void sendJSON(int d) {
    String s = "{";
    s += "\"keypress\":" + String(int(d));
    s += "}";
    Serial.println(s);
}

void readJSON(String str) {
  char json[50];
  str.toCharArray(json, 50);
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.parseObject(json);
  double action = root["action"];
  Serial.println(action);
  if (action==1) {
    digitalWrite(LED_BUILTIN, HIGH);  
  } else if (action==2) {
    digitalWrite(LED_BUILTIN, LOW);  
  }
}

void loop() {  
  buttonState = digitalRead(buttonPin);
  if (buttonState == HIGH) {
    sendJSON(40);
  }
  
  while (Serial.available() > 0) {
    readJSON(Serial.readString());
  }
  delay(300);
}









