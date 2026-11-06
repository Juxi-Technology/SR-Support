---
title: 10 参考：模型、参数与许可
description: 参考模型文件（MuJoCo XML / STL）、固件参数表、四姿态参考序列、验证状态与许可。
---

# 10 参考：模型、参数与许可

## 10.1 参考模型文件

仿真采用 MuJoCo MJCF（`.xml` + `.stl` 网格），与实机同源（自研 v1 设计）：

| 文件 | 说明 |
|---|---|
| `hardware/v1/robot_v1.xml` | 主模型（与实机几何/质量对应） |

| `hardware/v1/meshes/*.stl` | 6 个网格（底座底板/外壳、肩座、上臂支架、肘舵机、小臂杆） |
| `hardware/v1/meshes/print_mass_model.json` | 逐件打印质量表（15% 填充） |


本仓库未附带 URDF；如需 ROS 使用，可由上述 CAD/网格导出。

## 10.2 固件关键参数（`firmware/sr_support_b_ptk/include/config.h`）

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
| `SERVO_SHOULDER_CENTER_US` | 1681 | 肩零点脉宽（2026-11 视觉中位固化；以 [02 页](./02-zero-tool) 定零为准） |
| `SERVO_CENTER_US` | 1456 | 肘零点脉宽（同上） |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | 肩手动命令限位 |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | 手动范围（执行器机械行程 ±1.55） |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | 舵机方向 |
| `IMU_YAW90` | 1 | IMU 安装偏转 90° 的坐标换算 |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | 姿态滤波：加速度修正增益 / 信任带 |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | 热点（`w` 开关，上电默认开） |

## 10.3 参考序列（肩, 肘，rad；与 `training/b_line/getup_reference_b39.py` 逐值同步）

| 姿态 | 序列 |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → 收臂` |
| `roll_neg` | `[-1.80,0.70]` 全速直接按压（保持 ≤40 拍）→ 楔形泵 `[-1.80,0.35] → [-1.80,0.05]` ×2（各保持 ≤30 拍）→ 兜底：`[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]`（鞭甩下砸，保持 ≤40 拍）→ 收尾保持 ≤90 拍 → 收臂 |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → 收臂` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → 收臂` |

## 10.4 验证状态与出厂检验（2026-11-06）

- **出厂检验**：每台成品在出厂前完成——舵机零点按 [02 页](./02-zero-tool) 逐台定零并固化、
  IMU 陀螺与加速度计零点标定（NVS）、四方向扶正逐台测试通过；
- 四个方向实机扶正全部通过，均为**直接起身**（无需翻滚），约 1–6 秒，全程无舵机越界；
- `roll_neg` 最终方案：全行程直接按压 + 肘部楔形泵 ×2，失败时鞭甩下砸重试（早期依赖
  "滚过顶部 + 姿态重规划"的方案已废弃）；
- 状态机另经 IMU 加速度计零点标定修正（见 [03 调试页 3.2](./03-debug-and-checks)），
  躺姿姿态与实际一致；
- 仿真 1× 质量模型下 `roll_neg` 不复现（模型手臂质量/摩擦与实机不同），属已知模型差异，
  实机固件以实机验证为准。

## 10.5 许可与来源

- B 线固件/训练代码：MIT / Apache-2.0；
- B 线 CAD/STL：CERN-OHL-S-2.0（强互惠，商用前确认义务）；
- SelfRisingRobot：无许可证，本教程不包含其代码、waypoint 或模型文件；
- 专利 CN109693729A/B：商用前需完成 FTO 评估。
