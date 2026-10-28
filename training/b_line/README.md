# training/b_line — B 线（PTK7452MG，180° PWM）训练/评估/导出

> 本目录基于 Juxi-Technology/2dof-selfrighting-robot 的 B 线仿真代码（MIT/Apache-2.0）。
> 默认机型 **`selfrising`**：按用户实机的 SelfRisingRobot 3D 打印件重建（`assets/robot_selfrising.xml`），
> 5 个打印件 + 2× PTK7452MG + 电控盒，整机约 **97 g**；舵机力矩按 **3.4 kg·cm @6V（0.333 N·m）**。
> 旧的 Juxi B 线几何保留为 `robot_ptk7452`，只做对照。
>
> 来源/许可见 [`../../third_party/juxi-2dof/`](../../third_party/juxi-2dof/)、[`../../docs/provenance.md`](../../docs/provenance.md)；
> STL 来自 SelfRisingRobot（**无许可证**，仅本地仿真、不可再分发）。

## 1. 文件

| 文件 | 作用 |
|---|---|
| `selfright_env.py` | MuJoCo/Gymnasium 环境：10 维观测、2 维动作、DR、50Hz |
| `assets/robot_selfrising.xml` | **默认机型**：用户实机 3D 打印件 + PTK7452，由 `tools/build_selfrising_model.py` 生成 |
| `assets/selfrising/*.stl` | 重新居中/缩放的零件网格 + 质量/惯量参数（本地仿真用，不再分发） |
| `assets/robot_ptk7452.xml` | Juxi B 线几何，保留作对照 |
| `train.py` | PPO 训练，默认 128×128、3M 步 |
| `evaluate.py` | 成功率评估（标称/DR/逐面） |
| `play.py` | 打开 MuJoCo 窗口看策略/随机动作；默认站起后归位并保持 |
| `stand_homer.py` | 站立归位控制器：站稳 1 s 后把目标角缓慢归零（手臂竖直）并保持 |
| `pretrain_teachers.py` | 逐面教师策略蒸馏 + PPO 微调（可选，B 线推荐） |
| `export_policy.py` | 导出 `policy_b.h`，可选 C/PyTorch 逐点校验 |
| `policy_stdin.c` | C 校验脚手架 |

## 2. 安装

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r training/b_line/requirements.txt
```

## 3. 先跑通仿真

```bash
python -m training.b_line.train --robot selfrising --smoke --n-envs 2
```

冒烟训练只跑少量步数，确认 XML、Gym、SB3 都能加载。

## 4. 训练

从零训练（4 姿态 + DR）：

```bash
python -m training.b_line.train --robot selfrising --steps 3000000 --n-envs 8 --hidden 128
```

Juxi B 线的经验是 **128×128** 才覆盖四面；64×64 只学会部分姿态。显存/内存不足就减 `--n-envs`。

> Windows 上默认用 `DummyVecEnv`（顺序执行），避免多进程 pickle 问题；8 个 env 会比 Linux/macOS 的 `SubprocVecEnv` 慢，必要时减到 2–4。  
> 训练前先把实际打印件称重，改 `tools/build_selfrising_model.py` 里的 `MASS_*` 后重跑，再重新生成 `assets/robot_selfrising.xml`；否则仿真成功率不可信。

逐面教师 + 蒸馏（更接近 Juxi B 线配方，推荐）：

```bash
python -m training.b_line.train --robot selfrising --poses roll_pos   --run-name ppo_selfrising_roll_pos   --hidden 128 --steps 2000000
python -m training.b_line.train --robot selfrising --poses roll_neg   --run-name ppo_selfrising_roll_neg   --hidden 128 --steps 2000000
python -m training.b_line.train --robot selfrising --poses pitch_pos  --run-name ppo_selfrising_pitch_pos  --hidden 128 --steps 2000000
python -m training.b_line.train --robot selfrising --poses pitch_neg  --run-name ppo_selfrising_pitch_neg  --hidden 128 --steps 2000000

python -m training.b_line.pretrain_teachers --robot selfrising --hidden 128 --steps 2000000 \
  --teachers roll_pos=training/b_line/models/ppo_selfrising_roll_pos/final.zip,\
roll_neg=training/b_line/models/ppo_selfrising_roll_neg/final.zip,\
pitch_pos=training/b_line/models/ppo_selfrising_pitch_pos/final.zip,\
pitch_neg=training/b_line/models/ppo_selfrising_pitch_neg/final.zip
```

> 这条流程**不使用** SelfRisingRobot 的 waypoint 数值，也不复制它的代码；教师策略由本项目自己训练。仓库自带的 `policy_b.h` 是 Juxi 用 PTK7465 训练的策略，只能作为 bring-up 基线，**不要当成最终 PTK7452 策略**。

## 5. 评估

```bash
python -m training.b_line.evaluate --robot selfrising --episodes 100
python -m training.b_line.evaluate --robot selfrising --episodes 100 --dr --per-face
python -m training.b_line.evaluate --robot selfrising --episodes 100 --home
python -m training.b_line.evaluate --robot selfrising --episodes 100 --dr --per-face --home
```

结果写到 `training/b_line/models/eval_selfrising_*.json`。重点看 **DR + per-face**，不要只看标称。
`--home` 表示启用站立归位，成功判定要求最后 `|q| < 0.12`（手臂竖直）。

## 6. 导出到固件

```bash
python -m training.b_line.export_policy --robot selfrising --model training/b_line/models/ppo_selfrising_v2/final.zip
# 可选：需要本机 clang 才跑 C/PyTorch 逐点校验
python -m training.b_line.export_policy --robot selfrising --model training/b_line/models/ppo_selfrising_v2/final.zip --verify
```

默认输出：`firmware/sr_support_b_ptk/include/policy_b.h`。重新编译固件即可。

## 7. 观测/动作（必须和固件一致）

```
obs = [up_b(3), omega(3), q(2), qdot(2)]   # 10 维
action = [-1,1]^2 -> target = action * 1.55 rad
每 20 ms 目标最多变化 0.12 rad（6 rad/s）
```

固件 `main.cpp` 的 `POLICY_OBS_DIM` 必须是 10，`Q_HALF_RANGE` 1.55，`MAX_CMD_RATE` 0.12。

**成功判定**：
- 策略的 `info["upright"]`：`up_z > 0.90` 且脚座高度 ±30 mm（只要求扶正）。
- 最终竖直姿态由 `StandHomer` 微调：机身 `up_z>0.95` 连续 10 个控制周期（0.2 s）后，以 **0.12 rad/step** 把目标角归零并保持；收臂中 `up_z<0.95` 自动暂停，`up_z<0.90` 交回策略。v2 策略本身已经在起立过程中把手臂带到 q≈0.1–0.35，微调只需 0.06–0.10 s。
- `evaluate.py --home` 的成功判定额外要求最后 25 步 `|q| < 0.12`（手臂竖直向上，即装配姿态）。

## 8. PTK7452 / 实机 sim2real 重点

- 模型执行器现在是 **kp=50 / kv=0.5**，对应 PTK7452 这种“硬”位置舵机；早期 kp=2 的软执行器策略在实机会抖（仿真里 kp≥10 时 v2 成功率 0/10）。
- 模型力矩按 **3.4 kg·cm @6V（0.333 N·m）**；7.4V（约 4.5 kg·cm）可把 forcerange 改到 0.44 再重训，或先按 0.333 保守训练。
- 仿真实机质量 **97.4 g**（打印件约 51 g + 2×舵机 24.4 g + 电控盒 22 g）。这是估值：**打印后逐件称重**，改 `tools/build_selfrising_model.py` 里的 `MASS_*`，重跑生成 XML 再训练；否则仿真成功率不可信。
- 几何来自用户实机 STL：脚座 60×72.9 mm、肩轴高 25.4 mm、肘轴高 70.4 mm、直立总高 168 mm。比 Juxi B 线（287 mm）矮很多，重心更低。
- 静态测试：从四个倒地姿态出发，只保持一组固定关节角就能把 `up_z` 撑到 1.0（底板高度回到 0），说明 **0.333 N·m 足够**、机构可自起立；POLICY 要学的是任意姿态下选对动作。
- 固件没有舵机位置反馈，q/qdot 是指令角/指令角速度；如果舵机卡住，策略不会知道。确保机械行程无干涉，保留急停。
- 先空载/手扶测试，再落地；保留 `x` 释放 PWM 和电源开关。

## 9. 许可

- 仿真代码：基于 Juxi MIT/Apache-2.0；保留 [`../../third_party/juxi-2dof/`](../../third_party/juxi-2dof/)。
- 训练流程/奖励/导出脚本为本地修改或独立编写；未使用 SelfRisingRobot 的代码、权重或 waypoint。
- `assets/selfrising/*.stl` 来自用户本地 SelfRisingRobot 3D 模型，**无许可证**：仅本地仿真自己实机，不随产品/公开仓库分发；商用需作者许可或按实测尺寸重画。
- 硬件若使用 Juxi B 线 CAD/STL，属于 CERN-OHL-S-2.0（强互惠）；商用/分发前确认义务，或自行重画。

## 10. 本机实测（2026-10-22）

| 项目 | 结果 |
|---|---|
| Python | 3.12.9 |
| MuJoCo | **3.16.0** |
| Gymnasium | 1.4.0 |
| Stable-Baselines3 | 2.9.0 |
| PyTorch | 2.14.1+cpu |
| NumPy | 2.5.4 |
| 默认模型 | **`selfrising`**：5 个打印件 + 2×PTK7452 + 电控盒，**97.4 g** |
| 环境 reset + 100 步 | 通过（10 维 obs、2 维动作、无异常） |
| 静态起立检查 | 四个倒地姿态均可用一组固定关节角把 `up_z` 撑到 1.0（底板回正） |
| PPO 冒烟 | 40,960 步，约 28 s（旧 Juxi 几何，1428 fps） |
| **正式训练（v1 扶正）** | 500,000 步，4 env，128×128，约 7 min，`models/ppo_selfrising/final.zip` |
| **v1 + StandHomer** | 标称 96.7%（策略单独）；加归位后 100%，但手臂是“站住后再抬起” |
| **v2（扶正+收臂一体）** | 从 v1 续训 1M 步，`models/ppo_selfrising_v2/final.zip`；机身一正，手臂在 0.3–0.5 s 内回到竖直附近（q 0.1–0.35） |
| **v2 + 微调归位** | 标称 24/24（四方向各 6/6），微调只需 0.06–0.10 s；**但实机舵机比仿真硬，v2 在硬舵机模型下 0/10** |
| **v5（硬舵机重训）** | 模型执行器改为 **kp=50 / kv=0.5**（接近 PTK7452 实际刚度），从 v2 续训 1M 步：**标称 90%、DR 90%**；逐面 83/100/100/100%（n=6）；`models/ppo_selfrising_v5/final.zip` |
| **v7（SelfRisingRobot 慢接口）** | 观测 **5 维** `[up(3), q_target(2)]`（无陀螺/qdot），动作 = **目标角增量 ×0.08 rad/step**；标称/DR **100%**，四方向各 100%，类实机条件 6/6；`models/ppo_selfrising_sr5/final.zip` |
| **v6（+死区/延迟 DR）** | 加入舵机死区 0–0.03 rad、指令延迟 0–100 ms、IMU 观测延迟 0–40 ms 的 DR，从 v5_pitchneg 续训 1M 步：DR **96.7%**；类实机条件（死区 0.02、60 ms、40 ms）四方向 **6/6**；`models/ppo_selfrising_v6/final.zip` |
| v4 | 因 DR 未恢复 `actuator_biasprm` 导致刚度漂移，训练失败；已修复，保留作记录 |
| MuJoCo 窗口 | v5：倒地 → 扶正同时收臂 → 竖直 → 保持；可鼠标推倒反复起立 |

快速验证命令：

```bash
.venv/Scripts/python.exe -m training.b_line.train --robot selfrising --smoke --n-envs 2
```

```bash
.venv/Scripts/python.exe -m training.b_line.evaluate --robot selfrising --episodes 30 --home
```

```bash
.venv/Scripts/python.exe -m training.b_line.evaluate --robot selfrising --episodes 30 --dr --per-face --home
```

看 MuJoCo 窗口（默认模型就是 v2，可鼠标 Ctrl+Shift+右键拖动推倒）：

```bash
.venv/Scripts/python.exe -m training.b_line.play --pose pitch_pos --episodes 0
```

> 默认 `--home --hold`：站起后手臂归位到竖直并保持，不重置。连续 60 s 验证 `up_z=1.0`、`q=(0,0)`。
> 想反复看“倒地→起立”，加 `--no-hold`；只看策略原始行为加 `--no-home`；指定起始姿态用 `--pose ...`。

> 这是按**估算质量**训练的结果（打印件 51 g + 舵机 24.4 g + 电控 22 g）。实机打印后逐件称重、改 `MASS_*` 重新生成 XML 再训练，才是可用于部署的最终策略。
