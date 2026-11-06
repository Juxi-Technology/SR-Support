# B 线方案（2026-10-20 决定）

> 注（2026-11 瘦身）：文中出现的 `hardware/juxi_b_line/`、`bom/`、`firmware/sr_support_2dof/`、旧仿真模型与变体 XML 已从仓库移除，相关描述仅作历史记录；当前模型见 [`hardware/v1/`](../hardware/v1/)。

> **第一次做请按 [`build-guide.md`](build-guide.md) 的 0→12 阶段执行**；一页检查清单见 [`checklist.md`](checklist.md)。

> 决定：采用 Juxi-Technology/2dof-selfrighting-robot 的 **B 线**（2× PTK 180° PWM + 2R 臂 + IMU + RL），不再按之前“8 路/waypoint 骨架”作为主方案。  
> 硬件：ESP32-S3 + Juxi 6 轴 IMU + **无源直连舵机转接板** + 2× **PTK7452MG**（8 个中取 2 个）。  
> 目标：先做插电版 2-DOF 慢速/中速自起立样机；电池版后续再说。

## 1. 为什么选 B 线

- 你手上已经有 **8× PTK7452MG（180° PWM）**，B 线正好是同一类舵机，不需要再买 SCS 总线舵机。
- 转接板是**无源直连 + 共用舵机电源 + 级联排针**，不是 PCA9685；B 线固件直接出两路 50Hz PWM，最匹配。
- Juxi B 线已经有：CAD/STL、PlatformIO 固件、MuJoCo 环境、PPO 训练/评估/导出、sim2real 文档；代码 MIT/Apache-2.0，硬件 CERN-OHL-S-2.0，边界比 SelfRisingRobot 清楚。
- A 线（SCS0009/SCS2332 300° 总线 + 反馈）仿真更强（99% DR），但要另买舵机+总线转接板，且固件链接 GPL-3.0 SCServo；先不作为 v0。

## 2. 我们复用了什么、改了什么

复用（保留许可/来源）：

- `firmware/sr_support_b_ptk/`：Juxi B 线固件（`main.cpp`、`servo_backend.h`、`servo_pwm.cpp`、`config.h` 框架、`policy_b.h` 基线）。
- `training/b_line/`：Juxi `selfright_env.py`、`train.py`、`evaluate.py`、`export_policy.py`、`pretrain_teachers.py`、B 线 MJCF。
- `hardware/juxi_b_line/`：Juxi B 线 CAD/STL/STEP。
- 许可/来源：`third_party/juxi-2dof/`（MIT/Apache + NOTICE）。

本地改动：

- 舵机参数改为 **PTK7452MG**：12.2 g，3.4 kg·cm @6V（0.333 N·m），1520 µs 中位，25T。
- 仿真模型 `robot_selfrising.xml`：按实机 SelfRisingRobot 打印件生成（5 件 + 2×PTK7452 + 电控盒，约 97.4 g）；力矩 ±0.333 N·m；默认机器人 `selfrising`。Juxi 几何 `robot_ptk7452.xml` 仅作对照。
- 训练默认 **128×128**（Juxi B 线经验：64×64 覆盖不了四面）。
- 固件 LEDC API 兼容 Arduino-ESP32 2.x/3.x；新增 `x`（释放 PWM）和 `r`（重新初始化）命令。
- 训练/评估/导出脚本改为 `training/b_line` 独立包，默认模型/输出路径指向本项目。
- **不复制** Juxi 的 `expert_test.py` / `pretrain_scripted.py`（它们含 SelfRisingRobot 的 waypoint 数值）；我们的教师策略从零训练，不复用那些 waypoint。

## 3. 硬件连接

| 项目 | 连接 |
|---|---|
| IMU SDA | **GPIO6**（优先直连；转接板 CH3 信号脚实测不稳） |
| IMU SCL | **GPIO7**（优先直连；转接板 CH4 信号脚实测不稳） |
| IMU GND | CH3/CH4 的 GND 或 ESP32 GND |
| IMU VCC | **ESP32 3V3**；**不要接舵机口的 V+（6V），也不要接 5V5** |
| 肩舵机 | GPIO4（CH1，50Hz PWM） |
| 肘舵机 | GPIO5（CH2，50Hz PWM） |
| 备用 | GPIO15/16/17/18（CH5–CH8） |
| LED（可选） | GPIO2 |
| 舵机电源 | **6V/≥5A** 独立电源，V+ 接转接板电源轨，GND 与 ESP32 共地 |
| ESP32 | USB-C 5V，单独供电；不要用舵机 6V 给 ESP32 |
| 转接板 | 无源直连；确认每个级联排针的 V+/GND/信号顺序一致 |

> 转接板映射：CH1..CH8 = GPIO4、5、6、7、15、16、17、18。  
> 当前 CH1/CH2 给肩/肘；CH3/CH4 的信号脚改作 I²C SDA/SCL，**这两个口的 V+ 悬空不用**；CH5–CH8 备用。  
> 如果实际丝印顺序不同，以万用表通断为准，并改 `config.h` 的 `PIN_I2C_SDA/SCL` 和 `PIN_SERVO_*`。

## 4. 关键风险（必须正视）

1. **PTK7452 比 B 线训练用的 PTK7465 弱**：6V 3.4 vs 4.5 kg·cm。B 线 DR 已经只有 63%；直接用基线策略大概率更差。  
   - 方案 A：6V 先按 3.4 重训（推荐，安全）；  
   - 方案 B：7.4V/5A 运行（约 4.5 kg·cm），但发热/电流/寿命要实测，且仍建议重训。
2. **质量 gap**：仿真整机按 97.4 g（打印件 51 g + 舵机 24.4 g + 电控 22 g）。**打印后必须逐件称重、改 `MASS_*` 重新生成 XML 再训练**，否则仿真成功率没有意义。
3. **180° 行程 + 无位置反馈**：B 线靠 128×128 教师蒸馏覆盖四面；如果舵机卡住，固件不知道。机械必须无干涉，保留 `x`/电源开关。
4. **基线策略不是最终策略**：`policy_b.h` 是 PTK7465 的 Juxi 策略，只用于接线/台架；最终用 `training/b_line/` 重训。
5. **许可**：代码 MIT/Apache；硬件 CERN-OHL-S（强互惠）；B 线固件不链接 GPL SCServo。商用/分发前让法务确认 CERN 义务。

## 5. 落地顺序

1. **打印/装配**：用 `hardware/juxi_b_line/STL/b_*.stl`，PETG；量 PTK7452 实物，确认舵机座/舵盘/耳片。
2. **称重/量尺寸**：把实际质量、臂长、肩高填进 `tools/build_selfrising_model.py`，重新生成 `training/b_line/assets/robot_selfrising.xml`。
3. **固件 bring-up**：烧 `firmware/sr_support_b_ptk`；先只接 USB 看 IMU，再给舵机上电；`t` 自检方向，`s`/`x`/`r` 验证安全。
4. **基线策略试跑**：手扶、低预期，确认 `g` 后手臂动作方向正确；不要直接放手。
5. **重训**：按 [`training/b_line/README.md`](../training/b_line/README.md) 用实际质量/力矩训练 128×128；先逐面教师，再蒸馏 + PPO。
6. **评估**：`--dr --per-face`；目标先定 8/10，不要按 Juxi 的 96% 宣传。
7. **实机 100 次**：记录成功率、电流、温度、齿轮；再决定是否做 7.4V 或换 A 线。

## 6. 许可/来源

- 代码/仿真：Juxi-Technology/2dof-selfrighting-robot，MIT OR Apache-2.0；见 [`../third_party/juxi-2dof/`](../third_party/juxi-2dof/)。
- 硬件 CAD/STL：CERN-OHL-S-2.0；见 [`../hardware/juxi_b_line/`](../hardware/juxi_b_line/)。
- 不使用 SelfRisingRobot 的代码/STL/waypoint；基线 `policy_b.h` 只作 bring-up，最终策略由本项目训练。
- 完整来源记录：[`provenance.md`](provenance.md)。
