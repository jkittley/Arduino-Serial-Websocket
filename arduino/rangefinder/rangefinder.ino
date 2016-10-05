#include <ArduinoJson.h>

// Sensor pins
const int trigPin = 6;
const int echoPin = 5;

// Constants
const int   PULSE_TIMEOUT = 10000;    // Max time to wait for a sensor to respond
const int   BAUD_RATE     = 9600;     // Serial comms rate

void setup() {
  // initialize serial
  Serial.begin(BAUD_RATE);
  while (!Serial) {
    // Wait for serial to establish
  }
  Serial.println("{ \"status\":\"Online\"");
   
  // Trigger pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);
}

float microsecondsToMM(long microseconds) {
  return (microseconds / 58.2) * 10;
}

float dist(int trigPin, int echoPin) {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    return microsecondsToMM(pulseIn(echoPin, HIGH, PULSE_TIMEOUT));
}

void sendJSON(float d) {
    String s = "{";
    s += "\"d\":"     + String(int(floor(d)));
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
  float d = dist(trigPin, echoPin);
  sendJSON(d);
  while (Serial.available() > 0) {
    readJSON(Serial.readString());
  }
  delay(300);
}









