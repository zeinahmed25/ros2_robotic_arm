/*
 * arm_servos.ino
 *
 * Firmware for the ROS 2 robotic arm (Arduino Uno + 2x SG90 servos).
 *
 * Protocol (USB serial, 115200 baud, 8N1):
 *   PC -> Arduino : "<servo1_deg>,<servo2_deg>\n"    e.g. "90,45\n"
 *   Arduino -> PC : "READY\n" once at start-up,
 *                   "ERR\n" for every line that could not be parsed.
 *
 * Angles are integers in degrees. Values outside 0..180 are clamped.
 *
 * Wiring (see README):
 *   D9  -> servo 1 signal (base rotation, joint1)
 *   D10 -> servo 2 signal (shoulder,      joint2)
 *   Servo power comes from the external 5 V supply, NOT from the Arduino.
 *   External supply GND, servo GND and Arduino GND must be connected.
 */

#include <Servo.h>

const uint8_t NUM_SERVOS = 2;
const uint8_t SERVO_PINS[NUM_SERVOS] = {9, 10};
const int START_ANGLE = 90;       // centre position at power-up
const long BAUD_RATE = 115200;
const uint8_t LINE_BUF_SIZE = 32;

Servo servos[NUM_SERVOS];
char lineBuf[LINE_BUF_SIZE];
uint8_t lineLen = 0;

// Parse "a,b" into out[0], out[1]. Returns true on success.
bool parseLine(const char *line, long out[NUM_SERVOS]) {
  const char *p = line;
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    char *end;
    long v = strtol(p, &end, 10);
    if (end == p) {
      return false;               // no digits found
    }
    out[i] = v;
    p = end;
    if (i < NUM_SERVOS - 1) {
      if (*p != ',') {
        return false;             // missing separator
      }
      p++;
    }
  }
  return *p == '\0';              // nothing may follow the last number
}

void handleLine() {
  long angles[NUM_SERVOS];
  if (!parseLine(lineBuf, angles)) {
    Serial.println(F("ERR"));
    return;
  }
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    servos[i].write((int)constrain(angles[i], 0L, 180L));
  }
}

void setup() {
  Serial.begin(BAUD_RATE);
  for (uint8_t i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(SERVO_PINS[i]);
    servos[i].write(START_ANGLE);
  }
  Serial.println(F("READY"));
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      if (lineLen > 0) {
        handleLine();
      }
      lineLen = 0;
    } else if (c != '\r') {
      if (lineLen < LINE_BUF_SIZE - 1) {
        lineBuf[lineLen++] = c;
      } else {
        lineLen = 0;              // line too long: drop it
        Serial.println(F("ERR"));
      }
    }
  }
}
