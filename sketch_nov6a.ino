#include <Servo.h>

#define SERVO_PIN 9 // Define the servo control pin
Servo myServo;

int currentPosition = 90; // Track the current position of the servo
int targetPosition = 100;  // Track the target position of the servo
unsigned long lastMoveTime = 0; // Tracks the last time the servo moved
const unsigned long moveInterval = 1; // Adjust for speed; smaller values for faster movement

void setup() {
  Serial.begin(9600);
  myServo.attach(SERVO_PIN);
  myServo.write(currentPosition); // Initialize servo position to 0
}

void loop() {
  // Check if there's a new command from Python to control the servo
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    int position = command.toInt(); // Convert command to integer
    if (position >= 0 && position <= 180) {
      targetPosition = position; // Update target position immediately if a new command comes in
    }
  }

  // Move the servo incrementally towards the target position
  if (millis() - lastMoveTime >= moveInterval) {
    lastMoveTime = millis(); // Update the last move time

    // Gradually adjust the current position towards the target position
    if (currentPosition < targetPosition) {
      currentPosition++;
      myServo.write(currentPosition);
    } else if (currentPosition > targetPosition) {
      currentPosition--;
      myServo.write(currentPosition);
    }
  }
}
