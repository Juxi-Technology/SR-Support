/*
 * PTK7452MG servo center helper (ESP32-S3, 50 Hz PWM).
 *
 * Use this BEFORE assembling the arms:
 *   - connect only the two servo signal wires to GPIO4/5 (plus servo 6V power
 *     and common ground);
 *   - flash this sketch;
 *   - both servos output 1520 us (PTK neutral);
 *   - install the horns so both arms point straight up.
 *
 * Serial commands (115200):
 *   1 / 2   select shoulder / elbow
 *   + / -   nudge selected center by +10 / -10 us
 *   p       print current centers
 *
 * This sketch does not use the IMU and does not run a policy. It is only for
 * mechanical centering. Cut servo power before changing wiring.
 */

#include <Arduino.h>

#define PIN_SERVO_SHOULDER 4
#define PIN_SERVO_ELBOW 5

#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  #define SR_LEDC_NEW_API 1
#else
  #define SR_LEDC_NEW_API 0
#endif

static const int PINS[2] = {PIN_SERVO_SHOULDER, PIN_SERVO_ELBOW};
static const int CHANNELS[2] = {0, 1};
static float centerUs[2] = {1520.0f, 1520.0f};
static uint8_t selected = 0;
// ESP32-S3 LEDC max resolution is 14 bits.
#define SERVO_RES_BITS 14

static void writePulse(uint8_t i, float us) {
  if (us < 500.0f) us = 500.0f;
  if (us > 2500.0f) us = 2500.0f;
  uint32_t duty = (uint32_t)(us / 20000.0f * (float)((1u << SERVO_RES_BITS) - 1u));
#if SR_LEDC_NEW_API
  ledcWrite(PINS[i], duty);
#else
  ledcWrite(CHANNELS[i], duty);
#endif
}

static void writeBoth() {
  writePulse(0, centerUs[0]);
  writePulse(1, centerUs[1]);
}

static void printState() {
  Serial.printf("CH1(shoulder)=%.0fus  CH2(elbow)=%.0fus  selected=CH%u\n",
                centerUs[0], centerUs[1], (unsigned)(selected + 1));
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("PTK7452 center helper");
  Serial.println("Both servos -> 1520 us. Install horns with arms straight up.");
  for (int i = 0; i < 2; ++i) {
#if SR_LEDC_NEW_API
    if (!ledcAttach(PINS[i], 50, SERVO_RES_BITS)) {
      Serial.printf("ledcAttach failed on GPIO%d\n", PINS[i]);
    }
#else
    ledcSetup(CHANNELS[i], 50, SERVO_RES_BITS);
    ledcAttachPin(PINS[i], CHANNELS[i]);
#endif
  }
  writeBoth();
  printState();
  Serial.println("Commands: 1/2 select, +/- nudge 10us, p print");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '1') selected = 0;
    else if (c == '2') selected = 1;
    else if (c == '+') centerUs[selected] += 10.0f;
    else if (c == '-') centerUs[selected] -= 10.0f;
    else if (c == 'p') { printState(); continue; }
    else continue;
    if (centerUs[selected] < 1400.0f) centerUs[selected] = 1400.0f;
    if (centerUs[selected] > 1640.0f) centerUs[selected] = 1640.0f;
    writeBoth();
    printState();
  }
  delay(10);
}
