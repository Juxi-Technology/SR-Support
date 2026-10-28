// PTK7452MG/PWM servo backend (180 deg, no position feedback).
#include "config.h"

#ifdef ROBOT_PWM

#include <Arduino.h>

#include "servo_backend.h"

#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  #define SR_LEDC_NEW_API 1
#else
  #define SR_LEDC_NEW_API 0
#endif

namespace servo {
namespace {

const int CHANNELS[2] = {0, 1};
const int PINS[2] = {PIN_SERVO_SHOULDER, PIN_SERVO_ELBOW};
float g_signs[2] = {SERVO_SHOULDER_SIGN, SERVO_ELBOW_SIGN};
float g_center_us[2] = {SERVO_SHOULDER_CENTER_US, SERVO_CENTER_US};

float last_cmd[2] = {0.0f, 0.0f};

float clampf(float x, float lo, float hi) {
    return x < lo ? lo : (x > hi ? hi : x);
}

void write_q(const float q[2]) {
    for (int i = 0; i < 2; ++i) {
        float us = g_center_us[i] + g_signs[i] * q[i] * SERVO_US_PER_RAD;
        us = clampf(us, SERVO_MIN_US, SERVO_MAX_US);
        const uint32_t maxDuty = (1u << SERVO_RES_BITS) - 1u;
        uint32_t duty = (uint32_t)(us / 20000.0f * (float)maxDuty);
#if SR_LEDC_NEW_API
        ledcWrite(PINS[i], duty);
#else
        ledcWrite(CHANNELS[i], duty);
#endif
        last_cmd[i] = q[i];
    }
}

}  // namespace

bool begin(float q_init[2]) {
    for (int i = 0; i < 2; ++i) {
#if SR_LEDC_NEW_API
        // Re-arm after an 'r' command: ledcAttach() fails if the pin is
        // already attached, so detach and retry once.
        if (!ledcAttach(PINS[i], 50, SERVO_RES_BITS)) {
            ledcDetach(PINS[i]);
            if (!ledcAttach(PINS[i], 50, SERVO_RES_BITS)) return false;
        }
#else
        ledcSetup(CHANNELS[i], 50, SERVO_RES_BITS);
        ledcAttachPin(PINS[i], CHANNELS[i]);
#endif
    }
    q_init[0] = 0.0f;
    q_init[1] = 0.0f;
    write_q(q_init);
    delay(300);
    return true;
}

bool has_feedback() { return false; }

void set_signs(float shoulder, float elbow) {
    g_signs[0] = shoulder;
    g_signs[1] = elbow;
}

void get_signs(float out[2]) {
    out[0] = g_signs[0];
    out[1] = g_signs[1];
}

void set_center_us(int i, float us) {
    if (i >= 0 && i < 2) {
        g_center_us[i] = clampf(us, 400.0f, 2600.0f);
        write_q(last_cmd);
    }
}

float get_center_us(int i) {
    return (i >= 0 && i < 2) ? g_center_us[i] : 0.0f;
}

bool read(float q[2], float qd[2]) {
    (void)q;
    (void)qd;
    return false;
}

void write(const float q[2]) { write_q(q); }

void stop() { write_q(last_cmd); }

void release() {
    for (int i = 0; i < 2; ++i) {
#if SR_LEDC_NEW_API
        ledcDetach(PINS[i]);
#else
        ledcDetachPin(PINS[i]);
#endif
    }
}

void self_test() {
    Serial.println("self-test: +0.5, -0.5, neutral (0.9 s each)");
    const float seq[3] = {0.5f, -0.5f, 0.0f};
    for (int k = 0; k < 3; ++k) {
        float q[2] = {seq[k], seq[k]};
        write_q(q);
        delay(900);
    }
}

}  // namespace servo

#endif  // ROBOT_PWM
