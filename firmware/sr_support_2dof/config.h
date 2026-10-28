#pragma once
#include <Arduino.h>
#include "config.h"

// ============================================================
// SR-Support 2-DOF slow getup — 配置
// 板子：ESP32-S3（示例为 DevKitC-1；以实际板子 pinout 为准）
//
// 现有硬件：PTK 7452MG ×8 + ESP32-S3 舵机转接板（v0 只用 2 个舵机）。
// 引脚/通道映射待口述；参 docs/pinmap.md。以下 GPIO 只是示例。
//
// 舵机驱动：
//   SERVO_DRIVER_MODE 1 = 直连 GPIO，LEDC 产生 50Hz PWM（常见 3-pin 转接板）
//   SERVO_DRIVER_MODE 2 = PCA9685/I2C 16 通道 PWM 板（默认地址 0x40）
// ============================================================

// ---------------- 舵机驱动选择 ----------------
#define SERVO_DRIVER_MODE 1

// ---------------- I2C / IMU ----------------
// 注意：GPIO8/9 只是示例；如果转接板把 GPIO4-18 全部用于舵机，请改到空闲脚。
#define PIN_I2C_SDA        8
#define PIN_I2C_SCL        9

#define IMU_ADDR           0x23
#define I2C_HZ             100000
#define IMU_STARTUP_MS     5000
#define IMU_FAIL_TIMEOUT_MS 500

// ---------------- 8 路舵机 ----------------
#define SERVO_COUNT        8
#define SERVO_FREQ_HZ      50
// ESP32-S3 LEDC max resolution is 14 bits; 16 makes ledcAttach() fail.
#define SERVO_RES_BITS     14
#define PCA9685_ADDR       0x40

// 直连 GPIO 模式使用；PCA9685 模式下这些引脚被忽略（保留配置便于切换）。
// 示例映射：避开 I2C 8/9、USB 19/20、strapping 0/3/45/46。
// 实际以转接板丝印/你的口述为准；0xFF 表示该通道未使用。
static const uint8_t SERVO_PINS[SERVO_COUNT] = {
  4, 5, 6, 7, 10, 11, 12, 13
};

// 角色：0=肩，1=肘，2=辅助（v0 只用 0/1）
enum ServoRole : uint8_t {
  SERVO_ROLE_SHOULDER = 0,
  SERVO_ROLE_ELBOW    = 1,
  SERVO_ROLE_AUX      = 2
};
static const uint8_t SERVO_ROLES[SERVO_COUNT] = {
  SERVO_ROLE_SHOULDER, SERVO_ROLE_ELBOW,
  SERVO_ROLE_AUX, SERVO_ROLE_AUX,
  SERVO_ROLE_AUX, SERVO_ROLE_AUX,
  SERVO_ROLE_AUX, SERVO_ROLE_AUX
};

// 每路校准：角度 0 = 中位；+90°/-90° 映射到 MAX/MIN 脉宽。
// PTK 部分批次中位是 1520µs：把对应 CENTER 改 1520，或 OFFSET 加 +20。
static const uint16_t SERVO_MIN_US[SERVO_COUNT]    = {500, 500, 500, 500, 500, 500, 500, 500};
static const uint16_t SERVO_MAX_US[SERVO_COUNT]    = {2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500};
static const uint16_t SERVO_CENTER_US[SERVO_COUNT] = {1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500};
static const int16_t  SERVO_OFFSET_US[SERVO_COUNT] = {0, 0, 0, 0, 0, 0, 0, 0};
// 如果某个舵机转向和逻辑角度相反，把对应 SIGN 改成 -1.0f（不要反接电源）
static const float SERVO_SIGN[SERVO_COUNT] = {
  1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f
};

// 舵机目标限位/慢速起立步长
#define SERVO_TARGET_LIMIT_RAD  1.55f    // ±89°
#define SERVO_TARGET_DELTA_RAD  0.08f    // 每 20ms 最大变化（约 38rpm）
#define SERVO_UPDATE_MS         20

// 可选按键（低电平按下）；不用/与转接板冲突时改成 -1
#define PIN_BUTTON         14

// ---------------- 控制/状态机 ----------------
#define CONTROL_HZ          50
#define CONTROL_PERIOD_MS   20

#define FALL_TILT_RAD       0.75f    // 约 43°
#define FALL_CONFIRM_MS     300
#define DONE_TILT_RAD       0.25f    // 约 14°
#define DONE_HOLD_MS        700
#define GETUP_TIMEOUT_MS    14000
#define GETUP_HOLD_MS       400
#define AUTO_RETRY_MAX      3
#define AUTO_RETRY_COOLDOWN_MS 1500

// Waypoint 插值：每个 waypoint 段的时间
#define WAYPOINT_INTERP_MS  700
#define WAYPOINT_MAX        8

// ---------------- RL 策略（可选） ----------------
// 0 = 用 getup_sequence.h 的 waypoint（v0 默认）
// 1 = 用 training/export_policy.py 导出的 policy_network.h
#define USE_RL_POLICY       0
#define POLICY_ACTION_SCALE_RAD 0.08f

// ---------------- 调试 ----------------
#define SERIAL_BAUD         115200
#define PRINT_PERIOD_MS     100
