#include <Servo.h>

const int servoPins[5] = {9, 10, 11, 12, 13}; // Define the servo control pins
Servo servos[5];

int currentPositions[5] = {90, 90, 90, 90, 90}; // Initialize current positions
int targetPositions[5] = {90, 90, 90, 90, 90};  // Initialize target positions
unsigned long lastMoveTimes[5] = {0, 0, 0, 0, 0}; // Track last move times for each servo
const unsigned long moveInterval = 1; // Adjust for speed; smaller values for faster movement

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 5; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(currentPositions[i]); // Initialize servo positions to 90
  }
}

void loop() {
  // Check if there's a new command from Python to control the servos
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove any leading/trailing whitespace

    // Split the command by comma
    int commaIndex = command.indexOf(',');
    if (commaIndex > 0) {
      String servoStr = command.substring(0, commaIndex);
      String positionStr = command.substring(commaIndex + 1);

      int servoNumber = servoStr.toInt();
      int position = positionStr.toInt();

      // Validate servo number and position
      if (servoNumber >= 1 && servoNumber <= 5 && position >= 0 && position <= 180) {
        int index = servoNumber - 1; // Array index from 0 to 4
        targetPositions[index] = position; // Update target position for the servo
      }
    }
  }

  // Move servos incrementally towards their target positions
  for (int i = 0; i < 5; i++) {
    if (millis() - lastMoveTimes[i] >= moveInterval) {
      lastMoveTimes[i] = millis(); // Update last move time for this servo

      // Gradually adjust the current position towards the target position
      if (currentPositions[i] < targetPositions[i]) {
        currentPositions[i]++;
        servos[i].write(currentPositions[i]);
      } else if (currentPositions[i] > targetPositions[i]) {
        currentPositions[i]--;
        servos[i].write(currentPositions[i]);
      }
    }
  }
}
