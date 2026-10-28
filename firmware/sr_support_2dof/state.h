#pragma once
#include <Arduino.h>

// 主状态机状态。放在头文件里，避免 Arduino 自动生成函数原型时
// 因自定义类型定义在 .ino 中而出现 "State does not name a type"。
enum State : uint8_t {
  ST_BOOT,
  ST_SELFTEST,
  ST_IDLE,
  ST_MANUAL,
  ST_FALLEN_CONFIRM,
  ST_GETUP,
  ST_HOLD,
  ST_DONE,
  ST_ABORT,
  ST_FAULT
};
