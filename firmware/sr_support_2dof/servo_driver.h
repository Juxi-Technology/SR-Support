#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "config.h"
#include "i2c_bus.h"

// ============================================================
// 舵机驱动抽象
//   SERVO_DRIVER_MODE 1 -> LedcServoDriver（直连 GPIO，50Hz PWM）
//   SERVO_DRIVER_MODE 2 -> Pca9685ServoDriver（I2C 16 通道 PWM 板）
//
// 两种实现都只暴露 writeMicroseconds(ch, us)，上层 ServoArm 不关心硬件。
// 直连模式兼容 Arduino-ESP32 2.x/3.x 的 LEDC API。
// ============================================================

#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  #define SR_LEDC_NEW_API 1
#else
  #define SR_LEDC_NEW_API 0
#endif

class ServoDriver {
 public:
  virtual ~ServoDriver() {}
  virtual bool begin() = 0;
  virtual void writeMicroseconds(uint8_t ch, uint16_t us) = 0;
  virtual void detach(uint8_t ch) = 0;
  virtual const char *name() const = 0;
  virtual bool ok() const = 0;
};

// ------------------------------------------------------------------
// 直连 GPIO：LEDC
// ------------------------------------------------------------------
class LedcServoDriver : public ServoDriver {
 public:
  bool begin() override {
    bool allOk = true;
    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) {
      _attached[ch] = false;
      uint8_t pin = SERVO_PINS[ch];
      if (pin == 0xFF) continue;
#if SR_LEDC_NEW_API
      if (!ledcAttach(pin, SERVO_FREQ_HZ, SERVO_RES_BITS)) {
        allOk = false;
        continue;
      }
#else
      ledcSetup(ch, SERVO_FREQ_HZ, SERVO_RES_BITS);
      ledcAttachPin(pin, ch);
#endif
      _attached[ch] = true;
    }
    _ok = allOk;
    return _ok;
  }

  void writeMicroseconds(uint8_t ch, uint16_t us) override {
    if (ch >= SERVO_COUNT || !_attached[ch]) return;
    const uint32_t maxDuty = (1u << SERVO_RES_BITS) - 1u;
    uint32_t duty = (uint32_t)(((uint64_t)us * maxDuty) / 20000ULL);
#if SR_LEDC_NEW_API
    ledcWrite(SERVO_PINS[ch], duty);
#else
    ledcWrite(ch, duty);
#endif
  }

  void detach(uint8_t ch) override {
    if (ch >= SERVO_COUNT || !_attached[ch]) return;
#if SR_LEDC_NEW_API
    ledcDetach(SERVO_PINS[ch]);
#else
    ledcDetachPin(SERVO_PINS[ch]);
#endif
    _attached[ch] = false;
  }

  const char *name() const override { return "LEDC"; }
  bool ok() const override { return _ok; }

 private:
  bool _attached[SERVO_COUNT] = {false};
  bool _ok = false;
};

// ------------------------------------------------------------------
// PCA9685：I2C 16 通道 PWM
// ------------------------------------------------------------------
class Pca9685ServoDriver : public ServoDriver {
 public:
  bool begin() override {
    _ok = false;
    if (!srI2cBegin()) return false;

    // MODE1: 正常 -> sleep -> 写 prescale -> 唤醒 -> RESTART + AI
    if (!write8(REG_MODE1, 0x00)) return false;
    if (!write8(REG_MODE1, 0x10)) return false;  // SLEEP
    uint8_t prescale = (uint8_t)((25000000.0 / (4096.0 * SERVO_FREQ_HZ)) - 1.0 + 0.5);
    if (!write8(REG_PRESCALE, prescale)) return false;
    if (!write8(REG_MODE1, 0x00)) return false;
    delay(5);
    if (!write8(REG_MODE1, 0xA1)) return false;  // RESTART | AI | ALLCALL

    for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) {
      _attached[ch] = true;
      if (!writePwm(ch, 0, FULL_OFF)) return false;
    }
    _ok = true;
    return true;
  }

  void writeMicroseconds(uint8_t ch, uint16_t us) override {
    if (ch >= SERVO_COUNT || !_attached[ch]) return;
    uint32_t off = ((uint32_t)us * 4096u) / 20000u;  // 20ms 周期
    if (off > 4095u) off = 4095u;
    if (!writePwm(ch, 0, (uint16_t)off)) _ok = false;
  }

  void detach(uint8_t ch) override {
    if (ch >= SERVO_COUNT || !_attached[ch]) return;
    if (!writePwm(ch, 0, FULL_OFF)) _ok = false;
    _attached[ch] = false;
  }

  const char *name() const override { return "PCA9685"; }
  bool ok() const override { return _ok; }

 private:
  enum : uint8_t {
    REG_MODE1 = 0x00,
    REG_PRESCALE = 0xFE,
    REG_LED0_ON_L = 0x06
  };
  enum : uint16_t { FULL_OFF = 0x1000 };  // OFF_H 的 full-off 位

  bool _attached[SERVO_COUNT] = {false};
  bool _ok = false;

  bool write8(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(PCA9685_ADDR);
    Wire.write(reg);
    Wire.write(val);
    return Wire.endTransmission() == 0;
  }

  bool writePwm(uint8_t ch, uint16_t on, uint16_t off) {
    Wire.beginTransmission(PCA9685_ADDR);
    Wire.write((uint8_t)(REG_LED0_ON_L + 4 * ch));
    Wire.write((uint8_t)(on & 0xFF));
    Wire.write((uint8_t)(on >> 8));
    Wire.write((uint8_t)(off & 0xFF));
    Wire.write((uint8_t)(off >> 8));
    return Wire.endTransmission() == 0;
  }
};
