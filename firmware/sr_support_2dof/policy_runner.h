#pragma once
#include "config.h"

#if USE_RL_POLICY

#include <math.h>
#include "juxi_imu.h"
#include "servo_pair.h"

#if defined(__has_include)
  #if __has_include("policy_network.h")
    #include "policy_network.h"
  #else
    #error "USE_RL_POLICY=1 但 policy_network.h 不存在；先运行 training/export_policy.py"
  #endif
#else
  #include "policy_network.h"
#endif

#if !defined(POLICY_READY) || (POLICY_READY == 0)
  #error "policy_network.h 未训练/未导出（POLICY_READY=0）；先运行 training/export_policy.py"
#endif

// ============================================================
// 训练策略部署（可选）
// - 训练脚本导出 6 -> 64 -> 64 -> 2 MLP 到 policy_network.h
// - observation: [rollAcc, pitchAcc, s1, s2, s1_vel, s2_vel]
// - action: 两路目标角增量，[-1,1] * POLICY_ACTION_SCALE_RAD
// - 默认 USE_RL_POLICY=0，先用 waypoint；训练好后再打开
// ============================================================

class PolicyRunner {
 public:
  void reset(const ServoArm &arm) {
    _target1 = arm.currentRad(0);
    _target2 = arm.currentRad(1);
    _prev1 = _target1;
    _prev2 = _target2;
    _first = true;
  }

  void step(const JuxiImuData &d, ServoArm &arm) {
    float s1 = arm.currentRad(0);
    float s2 = arm.currentRad(1);
    if (_first) {
      _prev1 = s1;
      _prev2 = s2;
      _first = false;
    }

    const float dt = CONTROL_PERIOD_MS / 1000.0f;
    float v1 = constrain((s1 - _prev1) / dt, -20.0f, 20.0f);
    float v2 = constrain((s2 - _prev2) / dt, -20.0f, 20.0f);
    _prev1 = s1;
    _prev2 = s2;

    static_assert(POLICY_OBS_DIM == 6, "policy obs layout must be 6");
    static_assert(POLICY_ACT_DIM == 2, "policy action layout must be 2");

    float obs[POLICY_OBS_DIM] = {
      d.rollAccRad, d.pitchAccRad, s1, s2, v1, v2
    };
    float act[POLICY_ACT_DIM] = {0.0f, 0.0f};
    policyForward(obs, act);

    _target1 = constrain(_target1 + act[0] * POLICY_ACTION_SCALE_RAD,
                         -SERVO_TARGET_LIMIT_RAD, SERVO_TARGET_LIMIT_RAD);
    _target2 = constrain(_target2 + act[1] * POLICY_ACTION_SCALE_RAD,
                         -SERVO_TARGET_LIMIT_RAD, SERVO_TARGET_LIMIT_RAD);
    arm.setTargetsRad(_target1, _target2);
  }

 private:
  float _target1 = 0.0f;
  float _target2 = 0.0f;
  float _prev1 = 0.0f;
  float _prev2 = 0.0f;
  bool _first = true;
};

#endif  // USE_RL_POLICY
