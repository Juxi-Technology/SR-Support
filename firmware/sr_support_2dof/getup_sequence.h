#pragma once
#include <Arduino.h>
#include <math.h>
#include "config.h"

// ============================================================
// 4 种倒地姿态的 waypoint 起立序列
//
// 重要：
// - 下面目前是 **占位值 {0,0}**，不会产生动作；机械装好后必须按实测整定。
// - 每个 waypoint 是两个舵机的目标角（弧度）：0=中位，±1.55≈±89°。
// - 最后一个 waypoint 建议 {0,0}（起立后臂回到中位）。
// - 不要直接复制 SelfRisingRobot 的 waypoint/STL（无许可证）；自行整定。
//
// 整定方法（建议）：
// 1. 手动模式把机器人摆成某一倒姿；
// 2. 用 a/d/j/l 慢慢移动两个舵机，观察机身如何被撑起；
// 3. 记录关键角度，填入对应序列；
// 4. 从单姿态开始，跑通后再做 4 姿态。
// ============================================================

// v0 安全开关：waypoint 未整定时保持 0，固件不会自动起立，g 也会被拒绝。
// 把下面的 GETUP_SEQ 填好、并在实机上验证后，再改成 1。
#define GETUP_SEQ_READY 0

enum FallPose : uint8_t {
  POSE_FRONT = 0,
  POSE_BACK  = 1,
  POSE_LEFT  = 2,
  POSE_RIGHT = 3,
  POSE_UNKNOWN = 255
};

struct Waypoint {
  float s1;  // servo 1 target (rad)
  float s2;  // servo 2 target (rad)
};

// 安装方向修正：如果前后/左右判断反了，把对应 SIGN 改成 -1.0f
#define POSE_ROLL_SIGN   1.0f
#define POSE_PITCH_SIGN  1.0f

static inline FallPose classifyFallPose(float rollRad, float pitchRad) {
  float r = rollRad * POSE_ROLL_SIGN;
  float p = pitchRad * POSE_PITCH_SIGN;
  if (fabsf(r) > fabsf(p)) {
    return (r > 0.0f) ? POSE_LEFT : POSE_RIGHT;
  }
  return (p > 0.0f) ? POSE_FRONT : POSE_BACK;
}

// TODO: 用实测 waypoint 替换下面的 {0,0}；长度按需增加（<= WAYPOINT_MAX）。
static const Waypoint GETUP_SEQ[4][WAYPOINT_MAX] = {
  // POSE_FRONT
  { {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f},
    {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f} },
  // POSE_BACK
  { {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f},
    {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f} },
  // POSE_LEFT
  { {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f},
    {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f} },
  // POSE_RIGHT
  { {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f},
    {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f}, {0.0f, 0.0f} }
};

// 每个姿态的有效 waypoint 数（占位阶段先用 1，避免误动作）
static const uint8_t GETUP_SEQ_LEN[4] = {1, 1, 1, 1};
