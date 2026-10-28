// PTK7452MG servo test for the B-line adapter board.
//
// Signals:
//   shoulder -> GPIO4 (CH1)
//   elbow    -> GPIO5 (CH2)
// Servo V+ must be the 6 V rail; GND common with ESP32.
//
// Safety: boot outputs 1520 us (neutral) and waits. Nothing moves until you
// send a command. Commands (115200):
//   1 / 2    select shoulder / elbow
//   + / -    nudge selected by +10 / -10 us (range 1400..1640)
//   t        slow sweep selected: center -> +0.35 rad -> -0.35 rad -> center
//   c        center both
//   p        print state
//
// Monitor with DTR/RTS low to avoid reset spam:
//   pio device monitor --rts 0 --dtr 0 -b 115200 -p COMx

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
static const float CENTER_US[2] = {1520.0f, 1520.0f};
static const float US_PER_RAD = 636.62f;
// ESP32-S3 LEDC max resolution is 14 bits; 16 makes ledcAttach() fail.
#define SERVO_RES_BITS 14

static float targetRad[2] = {0.0f, 0.0f};
static float currentRad[2] = {0.0f, 0.0f};
static uint8_t selected = 0;

static float clampf(float x, float lo, float hi) {
  return x < lo ? lo : (x > hi ? hi : x);
}

static void writePulse(uint8_t i, float rad) {
  float us = CENTER_US[i] + rad * US_PER_RAD;
  us = clampf(us, 500.0f, 2500.0f);
  uint32_t duty = (uint32_t)(us / 20000.0f * (float)((1u << SERVO_RES_BITS) - 1u));
#if SR_LEDC_NEW_API
  ledcWrite(PINS[i], duty);
#else
  ledcWrite(CHANNELS[i], duty);
#endif
}

static void writeBoth() {
  writePulse(0, currentRad[0]);
  writePulse(1, currentRad[1]);
}

static void printState() {
  Serial.printf("CH1/shoulder target=%+.3f rad (%.0f us) current=%+.3f | "
                "CH2/elbow target=%+.3f rad (%.0f us) current=%+.3f | selected=CH%u\n",
                targetRad[0], CENTER_US[0] + targetRad[0] * US_PER_RAD, currentRad[0],
                targetRad[1], CENTER_US[1] + targetRad[1] * US_PER_RAD, currentRad[1],
                (unsigned)(selected + 1));
}

static void centerBoth() {
  targetRad[0] = targetRad[1] = 0.0f;
  currentRad[0] = currentRad[1] = 0.0f;
  writeBoth();
}

static void sweepSelected() {
  const float seq[5] = {0.0f, 0.20f, 0.35f, 0.0f, -0.35f};
  Serial.printf("sweep CH%u: center -> +0.35 -> -0.35 -> center (slow)\n",
                (unsigned)(selected + 1));
  for (int k = 0; k < 5; ++k) {
    float start = currentRad[selected];
    float end = seq[k];
    for (int step = 1; step <= 40; ++step) {
      currentRad[selected] = start + (end - start) * (step / 40.0f);
      writeBoth();
      delay(20);
    }
    delay(300);
  }
  currentRad[selected] = 0.0f;
  targetRad[selected] = 0.0f;
  writeBoth();
  Serial.println("sweep done");
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("PTK7452 servo test: shoulder=GPIO4(CH1), elbow=GPIO5(CH2)");
  Serial.println("Boot neutral 1520 us; nothing moves until a command.");
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
  centerBoth();
  printState();
  Serial.println("Commands: 1/2 select, +/- nudge 10us, t sweep, c center, p print");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '1') { selected = 0; printState(); }
    else if (c == '2') { selected = 1; printState(); }
    else if (c == '+') { targetRad[selected] += 10.0f / US_PER_RAD; }
    else if (c == '-') { targetRad[selected] -= 10.0f / US_PER_RAD; }
    else if (c == 'c') { centerBoth(); printState(); }
    else if (c == 'p') { printState(); }
    else if (c == 't') { sweepSelected(); printState(); }
    else continue;

    if (c == '+' || c == '-') {
      targetRad[selected] = clampf(targetRad[selected], -0.35f, 0.35f);
      currentRad[selected] = targetRad[selected];
      writeBoth();
      printState();
    }
  }
  delay(5);
}
