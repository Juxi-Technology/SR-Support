#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// ============================================================
// 共享 I2C 初始化
// - Juxi IMU（0x23）和 PCA9685（0x40）共用同一条 I2C
// - 只初始化一次；后续调用直接返回
// ============================================================
inline bool srI2cBegin() {
  static bool begun = false;
  if (begun) return true;
  begun = Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  if (begun) Wire.setClock(I2C_HZ);
  return begun;
}
