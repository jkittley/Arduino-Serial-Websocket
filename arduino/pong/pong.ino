#include <ArduinoJson.h>
#include <Servo.h>

// Sensor pins
const int trigPin = 6;
const int echoPin = 5;

// Servo
const int servoPowerPin = 12;
int pos = 0;    // variable to store the servo position
Servo myservo;  // create servo object to control a servo

// Constants
const int   PULSE_TIMEOUT = 10000;    // Max time to wait for a sensor to respond
const int   BAUD_RATE     = 9600;     // Serial comms rate

void setup() {
  Serial.begin(BAUD_RATE);
  while (!Serial) {
    // Wait for serial to establish
  }
  Serial.println("{ \"status\":\"Online\"");
   
  pinMode(servoPowerPin, OUTPUT);
  myservo.attach(9);
  
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
  if (action==1) {
    digitalWrite(LED_BUILTIN, HIGH);  
    myservo.write(180);              
    delay(100);  
    myservo.write(90);  
    delay(100); 
  } 
}

void loop() {  
//  digitalWrite(servoPowerPin, HIGH);
//   for (pos = 0; pos <= 180; pos += 1) { // goes from 0 degrees to 180 degrees
//    // in steps of 1 degree
//    myservo.write(pos);              // tell servo to go to position in variable 'pos'
//    delay(15);                       // waits 15ms for the servo to reach the position
//  }
//  for (pos = 180; pos >= 0; pos -= 1) { // goes from 180 degrees to 0 degrees
//    myservo.write(pos);              // tell servo to go to position in variable 'pos'
//    delay(15);                       // waits 15ms for the servo to reach the position
//  }
  float d = dist(trigPin, echoPin);
  sendJSON(d);
  while (Serial.available() > 0) {
    readJSON(Serial.readString());
  }
  delay(300);
}









