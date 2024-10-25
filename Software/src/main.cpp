#include <Arduino.h>

// put function declarations here:
int sensorPin = 2; // Pin connected to the phototransistor or photodiode
int detection = 0; // Variable to store the detection status

int analogPin = A2; // potentiometer wiper (middle terminal) connected to analog pin 2
                    // outside leads to ground and +5V
int val = 0;  // variable to store the value read

void setup() {

  pinMode(sensorPin, INPUT);
   // initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(9600); // Start serial communication

}

void loop() {
  detection = digitalRead(sensorPin); // Read the sensor value
  val = analogRead(analogPin);  // read the input pin
  Serial.println(val);
  digitalWrite(LED_BUILTIN,LOW);
  if (val <= 50) { // If the beam is broken
    Serial.println("Object detected!"); // Send a message to the serial monitor
    Serial.println(val);
    digitalWrite(LED_BUILTIN,HIGH);
    
  }
  delay(1000); // Short delay to avoid spamming the serial monitor
  
}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}