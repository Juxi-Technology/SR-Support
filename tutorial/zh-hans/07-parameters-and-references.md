---
title: 07 参数与参考
description: SR-Support 固件参数表、四姿态参考序列、验证状态与许可说明。
---

# 07 参数与参考

## 7.1 固件关键参数（`firmware/sr_support_b_ptk/include/config.h`）

| 参数 | 值 | 说明 |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | 50 Hz 控制周期 |
| `MAX_CMD_RATE` | 0.08 rad/拍 | 每拍输出限速（4 rad/s） |
| `FALL_UP_Z` | 0.30 | 跌倒门 up_z 阈值 |
| `FALL_W_QUIET` | 0.9 rad/s | 跌倒门角速度阈值 |
| `FALL_CONFIRM_TICKS` | 25 | 跌倒门确认拍数（0.5 s） |
| `EXEC_STEPS_PER_WP` | 20 | 每个参考路点拍数 |
| `EXEC_RETRACT_RATE` | 0.033 rad/拍 | 收臂速率 |
| `EXEC_DONE_TICKS` | 50 | 站立判定持续拍数 |
| `EXEC_TIMEOUT_MS` | 14000 | 单次参考超时 |
| `EXEC_COOLDOWN_TICKS` | 75 | 超时/完成后冷却（1.5 s） |
| `EXEC_SWITCH_TICKS` | 15 | 姿态切换确认拍数 |
| `EXEC_SWITCH_UP` | 0.60 | 切换时允许的最大 up_z |
| `EXEC_SWITCH_W` | 0.8 rad/s | 切换时允许的最大角速度 |
| `EXEC_MIN_SWITCH_AGE` | 25 | 参考启动后允许切换的最早拍数 |
| `EXEC_MAX_SWITCHES` | 5 | 单次运行最多切换次数 |
| `EXEC_NEUTRAL_MAX` | 120 | 中立回撤最长拍数 |
| `SERVO_SHOULDER_CENTER_US` | 1840 | 肩零点脉宽（换齿后） |
| `SERVO_CENTER_US` | 1520 | 肘零点脉宽 |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.07 / +2.07 rad | 肩可用行程 |
| `Q_ELBOW_MIN/MAX` | ±0.80 rad | 手动/策略范围（执行器机械行程 ±1.55） |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | 舵机方向 |
| `IMU_YAW90` | 1 | IMU 安装偏转 90° 的坐标换算 |

## 7.2 参考序列（肩, 肘，rad）

| 姿态 | 序列 |
|---|---|
| `roll_pos` | `[2.0,-0.8] → [0,-0.8] → [0,0]` |
| `roll_neg` | `[2.0,-0.8] ×4（保持）→ [0,-0.8] → [0,0]` |
| `pitch_pos` | `[-1.07,1.55] → [0,1.55] → [0,0]` |
| `pitch_neg` | `[-1.07,-1.55] → [0,-1.55] → [0,0]` |

## 7.3 验证状态（2026-10-27）

- 四个方向实机扶正均通过：`pitch_neg` ≈3 s、`pitch_pos` ≈5–6 s、`roll_pos` ≈3 s、
  `roll_neg` 5–14 s（滚过顶部 + 姿态重规划）；
- 全部测试无舵机越界；
- `roll_neg` 为实机专用序列：仿真 1× 模型的摩擦/质量与实机不同（实机手臂约等效 2× 质量），
  该方向在仿真中不复现，属已知差异而非代码不一致。

## 7.4 许可与来源

- B 线固件/训练代码：MIT / Apache-2.0；
- B 线 CAD/STL：CERN-OHL-S-2.0（强互惠，商用前确认义务）；
- SelfRisingRobot：无许可证，本教程不包含其代码、waypoint 或模型文件；
- 专利 CN109693729A/B：商用前需完成 FTO 评估。
