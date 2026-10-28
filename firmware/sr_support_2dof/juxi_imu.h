#pragma once
#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <string.h>
#include "config.h"
#include "i2c_bus.h"

// ============================================================
// Juxi 6 轴 IMU（I2C 0x23，100kHz，3.3V）
// - 欧拉角 0x26–0x31（float32 小端，弧度）
// - 加速度 0x04–0x09（int16 小端，16g）
// - 陀螺仪 0x0A–0x0F（int16 小端，2000°/s）
// - 无 Mag/BARO：不要读 0x10–0x15 / 0x32–0x41
// - tilt/azimuth 用加速度计，避免 Euler >90° 万向锁
// ============================================================

struct JuxiImuData {
  float rollRad = 0, pitchRad = 0, yawRad = 0;
  float rollDeg = 0, pitchDeg = 0, yawDeg = 0;
  float rollAccRad = 0, pitchAccRad = 0;  // 加速度计推导，用于倒地方向分类
  float ax = 0, ay = 0, az = 0;      // g
  float gx = 0, gy = 0, gz = 0;      // °/s
  float accelNorm = 1.0f;
  float tiltRad = 0;                 // 重力与机身 Z 轴夹角
  float azimuthRad = 0;              // 重力在 XY 平面的投影方向
  uint8_t version[3] = {0, 0, 0};
  bool valid = false;
};

class JuxiImu {
 public:
  bool begin(TwoWire &wire = Wire) {
    _wire = &wire;
    if (&wire == &Wire) {
      if (!srI2cBegin()) return false;
    } else {
      wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
      wire.setClock(I2C_HZ);
    }
    delay(10);
    return readVersion();
  }

  bool readVersion() {
    uint8_t b[3];
    if (!readBytes(0x01, b, 3)) return false;
    _d.version[0] = b[0];
    _d.version[1] = b[1];
    _d.version[2] = b[2];
    return true;
  }

  bool update() {
    uint8_t b[12];

    // 欧拉角（弧度）
    if (!readBytes(0x26, b, 12)) { _d.valid = false; return false; }
    _d.rollRad  = f32le(b + 0);
    _d.pitchRad = f32le(b + 4);
    _d.yawRad   = f32le(b + 8);
    if (!isfinite(_d.rollRad) || !isfinite(_d.pitchRad) || !isfinite(_d.yawRad)) {
      _d.valid = false;
      return false;
    }

    // 加速度（g）
    if (!readBytes(0x04, b, 6)) { _d.valid = false; return false; }
    _d.ax = i16le(b + 0) * 16.0f / 32767.0f;
    _d.ay = i16le(b + 2) * 16.0f / 32767.0f;
    _d.az = i16le(b + 4) * 16.0f / 32767.0f;

    // 陀螺仪（°/s）
    if (!readBytes(0x0A, b, 6)) { _d.valid = false; return false; }
    _d.gx = i16le(b + 0) * 2000.0f / 32767.0f;
    _d.gy = i16le(b + 2) * 2000.0f / 32767.0f;
    _d.gz = i16le(b + 4) * 2000.0f / 32767.0f;

    _d.rollDeg  = _d.rollRad  * RAD_TO_DEG;
    _d.pitchDeg = _d.pitchRad * RAD_TO_DEG;
    _d.yawDeg   = _d.yawRad   * RAD_TO_DEG;

    _d.accelNorm = sqrtf(_d.ax * _d.ax + _d.ay * _d.ay + _d.az * _d.az);
    if (_d.accelNorm < 0.01f) _d.accelNorm = 0.01f;

    // 用加速度计计算 tilt/azimuth（避免 Euler 万向锁）
    _d.tiltRad = acosf(constrain(_d.az / _d.accelNorm, -1.0f, 1.0f));
    _d.azimuthRad = atan2f(_d.ay, _d.ax);

    // 加速度计推导的 roll/pitch：用于倒地方向分类（Euler 仅调试）
    _d.rollAccRad = atan2f(_d.ay, _d.az);
    _d.pitchAccRad = atan2f(-_d.ax, sqrtf(_d.ay * _d.ay + _d.az * _d.az));

    _d.valid = true;
    return true;
  }

  const JuxiImuData &data() const { return _d; }

 private:
  TwoWire *_wire = nullptr;
  JuxiImuData _d;

  bool readBytes(uint8_t reg, uint8_t *buf, uint8_t len) {
    _wire->beginTransmission(IMU_ADDR);
    _wire->write(reg);
    if (_wire->endTransmission(false) != 0) return false;
    if (_wire->requestFrom((uint8_t)IMU_ADDR, (uint8_t)len, (uint8_t)true) != len) {
      return false;
    }
    for (uint8_t i = 0; i < len; i++) buf[i] = (uint8_t)_wire->read();
    return true;
  }

  static float f32le(const uint8_t *b) {
    uint32_t u = (uint32_t)b[0] | ((uint32_t)b[1] << 8) |
                 ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
    float f;
    memcpy(&f, &u, sizeof(f));
    return f;
  }

  static int16_t i16le(const uint8_t *b) {
    return (int16_t)((uint16_t)b[0] | ((uint16_t)b[1] << 8));
  }
};
