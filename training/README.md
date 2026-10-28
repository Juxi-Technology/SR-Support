# training — 旧 6 维骨架 / B 线训练入口

> **2026-10-20：当前主训练目录是 [`b_line/`](b_line/)**（Juxi B 线 10 维/128×128，PTK7452）。本目录的 `env_sr_2dof.py`/`train_ppo.py` 等是旧 6 维/64×64 骨架，保留作参考，不是当前主路径。
>
> 旧骨架的 MJCF/环境/脚本为本项目独立编写；没有复制 SelfRisingRobot 的代码/权重（无许可证）。当前 B 线的来源/许可见 [`../training/b_line/README.md`](b_line/README.md) 和 [`../docs/licensing.md`](../docs/licensing.md)。

## 1. 文件

| 文件 | 作用 |
|---|---|
| `assets/sr_2dof.xml` | 自建 MuJoCo 模型（机身 + 2 个铰链 + 脚；尺寸/质量是占位，需按你的 CAD 改） |
| `env_sr_2dof.py` | Gymnasium 环境：6 维 observation、2 维动作、奖励/终止 |
| `train_ppo.py` | PPO 训练（SB3），输出 `models/sr_ppo.zip` |
| `play.py` | 加载模型在 MuJoCo viewer 里跑 |
| `evaluate.py` | 跑 N 个 episode，统计仿真成功率（不替代实机） |
| `export_policy.py` | 旧骨架：导出 `6→64→64→2` MLP 到 `firmware/sr_support_2dof/policy_network.h`；B 线用 `b_line/export_policy.py` |
| `requirements.txt` | Python 依赖 |

## 2. 安装

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r training/requirements.txt
```

> MuJoCo 3.x 在 Windows/Linux/macOS 都有 wheel；如果 viewer 打不开，用 `--no-render` 或 `MUJOCO_GL=egl`（Linux headless）。

## 3. 训练

```bash
python training/train_ppo.py --timesteps 2000000 --n-envs 4
```

- 默认 `net_arch=[64,64]`、`Tanh`、`squash_output=True`；导出脚本依赖这个结构。
- 4 个并行环境；显存/内存不够就减 `--n-envs`。
- 训练日志在终端；模型保存到 `models/sr_ppo.zip`。
- 想换奖励/obs 就改 `env_sr_2dof.py`，但导出脚本要求 observation 仍是 6 维。

## 4. 看效果

```bash
python training/play.py --model models/sr_ppo.zip --episodes 3
```

无显示器：

```bash
python training/play.py --model models/sr_ppo.zip --no-render
```

统计仿真成功率：

```bash
python training/evaluate.py --model models/sr_ppo.zip --episodes 100
```

> 这里的“成功”是仿真里直立保持 0.5s 并结束回合；不等于实机成功率。实机要按需求文档的 4 姿态 × 10 次验收。

## 5. 导出到固件

```bash
python training/export_policy.py --model models/sr_ppo.zip
```

默认写入 `firmware/sr_support_2dof/policy_network.h`，然后：

1. 打开 `firmware/sr_support_2dof/config.h`，把 `USE_RL_POLICY` 改成 `1`。
2. 重新编译/烧录；`getup_sequence.h` 的 waypoint 不再使用。
3. 策略 observation 顺序必须与固件 `policy_runner.h` 一致：`[rollAcc, pitchAcc, s1, s2, s1_vel, s2_vel]`。
4. 动作是目标角增量：`action * 0.08 rad`，目标限幅 ±1.55 rad。

> `USE_RL_POLICY=1` 时必须存在 `policy_network.h`；否则编译会给出明确错误。默认 `0`，先用 waypoint 跑通硬件。

## 6. 环境设计（本项目自己的）

- **Observation（6）**：roll、pitch、肩角、肘角、肩角速度、肘角速度。
  - roll/pitch 在仿真里用**重力在机体系的投影**模拟加速度计（与固件 `rollAcc/pitchAcc` 的公式对齐），不是直接用四元数 Euler；但真实 IMU 还有噪声/线性加速度，sim-to-real 需要验证。
- **Action（2）**：两路目标角增量，`[-1,1]`，每 20ms 最多 `0.08 rad`；内部目标限幅 ±1.55 rad。
- **控制频率**：50Hz；物理步长 2ms，每步 10 个物理子步。
- **Reset**：85% 概率随机倒姿（roll/pitch 约 1.1–1.9 rad），15% 近直立；随机关节角；落地后先 settle 20 个物理步。
- **Reward**：
  - `exp(-4*tilt²)` 直立奖励；
  - 机身高度小奖励；
  - 动作幅值/关节速度/动作平滑惩罚；
  - 直立保持 0.5s 额外 +5 并结束回合；
  - 14s 超时截断。
- **Torque limit**：位置舵机 `forcerange=±0.30 N·m`，约 3 kg·cm，接近 PTK 7452MG 量级；实际齿轮/温度/电压会不同。

## 7. Sim-to-real 检查清单

- [ ] 用你的 CAD 尺寸/质量/重心更新 `assets/sr_2dof.xml`；至少量机身宽高、臂长、脚位置、总质量。
- [ ] 确认舵机中位/方向/行程与固件 `config.h` 一致（`SERVO_SIGN`、`CENTER_US`、`OFFSET_US`）。
- [ ] 旧骨架在固件里先跑手动模式，确认 50Hz 下舵机实际能跟上 `0.08 rad/20ms`；B 线当前是 `0.12 rad/20ms`（见 `b_line/`）。
- [ ] 加入延迟/噪声：真实 IMU 有噪声、滤波延迟；可以给 observation 加高斯噪声、给动作加 1–2 步延迟。
- [ ] 固件没有舵机位置反馈：`s1/s2` 用 `ServoArm` 的慢速命令角（`current`）近似实际关节角，速度也由命令角差分估计；仿真用真实 `qpos/qvel`。如果以后换总线舵机（HD-1910 等）并能读回位置，可改用真实角度，sim-to-real 会更准。
- [ ] 随机化质量/摩擦/舵机力矩（`model.body_mass`、`geom_friction`、`forcerange`），提高鲁棒性。
- [ ] 先在仿真里跑 100 次，统计成功率；实机先空载/低电压，再逐步提高。
- [ ] 策略输出在实机上先限幅/限速；保留急停 `x`。
- [ ] 本流程不使用 `VecNormalize`；如果你加了 observation 归一化，必须把 mean/std 一起导出，并在 C 端先归一化，否则 sim-to-real 会不一致。

## 8. 为什么不用作者的权重/环境

- SelfRisingRobot **没有许可证**，默认保留所有权利；它的代码、MJCF、权重、waypoint 不能复制/再分发/商用。
- 我们的 MJCF/奖励/观测/动作/训练脚本均为独立实现；即使方法相似，具体表达不同。
- 若你以后想直接用作者的文件，必须先取得书面商业许可，并保留授权记录。

## 9. 限制

- MJCF 是**模板**，不是你的最终机械；不更新尺寸/质量，sim-to-real 成功率没有意义。
- 没有建模舵机内部 PID、齿隙、死区、温度、电压跌落；这些需要实机标定/域随机化。
- 训练脚本/导出脚本**未在本机运行验证**（本环境没有安装 MuJoCo/SB3）；首次运行如遇 API 版本差异，按报错调整版本。
- 策略部署路径 `USE_RL_POLICY=1` 也**未实机验证**；先用 waypoint 跑通硬件，再切 RL。
