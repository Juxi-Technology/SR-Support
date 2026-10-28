#pragma once
#include <Arduino.h>
#include "config.h"
#include "servo_driver.h"

// ============================================================
// 8 通道舵机控制层（v0 只用 CH1/CH2 做 2-DOF 臂）
// - 角度 0 = 中位；±90° = 两端（按每路 MIN/MAX/CENTER/OFFSET 校准）
// - 慢速起立：每 20ms 最多变化 SERVO_TARGET_DELTA_RAD
// - 底层驱动由 SERVO_DRIVER_MODE 选择 LEDC 或 PCA9685
// ============================================================

class ServoArm {
 public:
  bool begin() {
    _running = false;
    if (!_driver.begin()) {
      for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) _driver.detach(ch);
      return false;
    }
    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) {
      _target[ch] = 0.0f;
      _current[ch] = 0.0f;
      writeChannel(ch);
    }
    if (!_driver.ok()) {
      for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) _driver.detach(ch);
      _running = false;
      return false;
    }
    _running = true;
    return true;
  }

  // 2-DOF 臂：CH1=肩，CH2=肘
  void setTargetsRad(float s1, float s2) {
    setChannelTargetRad(0, s1);
    setChannelTargetRad(1, s2);
  }

  void setTargetsDeg(float d1, float d2) {
    setTargetsRad(d1 * DEG_TO_RAD, d2 * DEG_TO_RAD);
  }

  void setChannelTargetRad(uint8_t ch, float rad) {
    if (ch >= SERVO_COUNT) return;
    _target[ch] = constrain(rad, -SERVO_TARGET_LIMIT_RAD, SERVO_TARGET_LIMIT_RAD);
  }

  void setChannelTargetDeg(uint8_t ch, float deg) {
    setChannelTargetRad(ch, deg * DEG_TO_RAD);
  }

  void moveChannelDeltaRad(uint8_t ch, float deltaRad) {
    if (ch >= SERVO_COUNT) return;
    setChannelTargetRad(ch, _target[ch] + deltaRad);
  }

  // 所有通道慢速回中
  void centerAllSlow() {
    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) _target[ch] = 0.0f;
  }

  // 立即回中（上电/复位用；会全速过去，机械未装好时注意）
  void centerImmediate() {
    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) {
      _target[ch] = 0.0f;
      _current[ch] = 0.0f;
      writeChannel(ch);
    }
  }

  void update() {
    if (!_running) return;
    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) {
      _current[ch] = slew(_current[ch], _target[ch]);
      writeChannel(ch);
    }
  }

  // 急停：所有通道停止 PWM（舵机卸力）。恢复需要再次 begin()。
  void stop() {
    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) _driver.detach(ch);
    _running = false;
  }

  bool attached() const { return _running; }
  float targetRad(uint8_t ch) const {
    return (ch < SERVO_COUNT) ? _target[ch] : 0.0f;
  }
  float currentRad(uint8_t ch) const {
    return (ch < SERVO_COUNT) ? _current[ch] : 0.0f;
  }
  float target1() const { return targetRad(0); }
  float target2() const { return targetRad(1); }
  float current1() const { return currentRad(0); }
  float current2() const { return currentRad(1); }

  const char *driverName() const { return _driver.name(); }
  bool driverOk() const { return _driver.ok(); }

 private:
#if SERVO_DRIVER_MODE == 2
  Pca9685ServoDriver _driver;
#else
  LedcServoDriver _driver;
#endif

  bool _running = false;
  float _target[SERVO_COUNT] = {0};
  float _current[SERVO_COUNT] = {0};

  static float slew(float current, float target) {
    float d = target - current;
    if (d > SERVO_TARGET_DELTA_RAD) d = SERVO_TARGET_DELTA_RAD;
    if (d < -SERVO_TARGET_DELTA_RAD) d = -SERVO_TARGET_DELTA_RAD;
    return current + d;
  }

  void writeChannel(uint8_t ch) {
    if (ch >= SERVO_COUNT) return;
#if SERVO_DRIVER_MODE != 2
    if (SERVO_PINS[ch] == 0xFF) return;  // 直连模式下该通道未接
#endif
    _driver.writeMicroseconds(ch, angleToPulse(ch, _current[ch]));
  }

  uint16_t angleToPulse(uint8_t ch, float rad) const {
    float deg = rad * SERVO_SIGN[ch] * RAD_TO_DEG;  // -89..89
    float halfSpan = (SERVO_MAX_US[ch] - SERVO_MIN_US[ch]) * 0.5f;
    float us = SERVO_CENTER_US[ch] + (deg / 90.0f) * halfSpan + SERVO_OFFSET_US[ch];
    int32_t v = (int32_t)(us + (us >= 0.0f ? 0.5f : -0.5f));
    if (v < (int32_t)SERVO_MIN_US[ch]) v = (int32_t)SERVO_MIN_US[ch];
    if (v > (int32_t)SERVO_MAX_US[ch]) v = (int32_t)SERVO_MAX_US[ch];
    return (uint16_t)v;
  }
};

// 兼容旧代码/旧文档中的类名
using ServoPair = ServoArm;
