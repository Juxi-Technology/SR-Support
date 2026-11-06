# SR-Support 2-DOF 慢速自起立机器人 工程需求文档

> 注（2026-11 瘦身）：文中出现的 `hardware/juxi_b_line/`、`bom/`、`firmware/sr_support_2dof/`、旧仿真模型与变体 XML 已从仓库移除，相关描述仅作历史记录；当前模型见 [`hardware/v1/`](../hardware/v1/)。

| 项目 | 内容 |
|---|---|
| 文档版本 | v0.3（草案） |
| 日期 | 2026-10-20 |
| 项目 | SR-Support / 2-DOF self-righting robot |
| 方案 | **B 线**：ESP32-S3 + Juxi 6 轴 IMU + 无源直连转接板 + 2× PTK7452MG（180° PWM） |
| 状态 | 待评审；B 线固件已编译/烧录；IMU/舵机/手动命令验证通过；**v2 策略已导出进固件并含站立收臂状态机**；实机已手动扶正；**实机质量仍为估算值（97.4 g），待称重重训** |
| 关联文档 | [b-line.md](b-line.md)、[pinmap.md](pinmap.md)、[licensing.md](licensing.md)、[provenance.md](provenance.md)、[applications.md](applications.md)、[hardware-validation.md](hardware-validation.md)、[../bom/bom.md](../bom/bom.md) |

> 本文件定义 **慢速/中速起立（post-fall recovery）** 方案的需求。  
> 不包含“倒下前快速打击（pre-active strike）”方案；后者需要 HD-1910-C001 级别总线舵机，另立需求。

---

## 0. B 线变更摘要（2026-10-20）

> 这一节优先于下文旧版（v0.2）的 8 路/waypoint 描述；当前实现以 [`b-line.md`](b-line.md)、[`../firmware/sr_support_b_ptk/`](../firmware/sr_support_b_ptk/) 和 [`../training/b_line/`](../training/b_line/) 为准。

- **执行器**：2× PTK7452MG，180° PWM，无位置反馈；转接板是**无源直连 + 共用 V+/GND + 级联**，不使用 PCA9685。
- **控制**：ESP32-S3 直接出 2 路 50Hz LEDC PWM（GPIO4/5）；I²C IMU（0x23/100kHz）在 **GPIO6/7**（转接板 CH3/CH4 信号脚）。
- **策略**：10 维观测 `[up(3), gyro(3), q(2), qdot(2)]` → 128×128 Tanh MLP → 2 维目标角；动作限速 **0.12 rad/20ms**；`Q_HALF_RANGE=1.55`。
- **电源**：舵机 **6V/≥5A**（PTK7452 约 3.4 kg·cm）；7.4V/5A 可选（约 4.5 kg·cm，注意发热）。
- **策略来源**：复用 Juxi B 线 MIT/Apache 代码/仿真；当前 `policy_b.h` 是 PTK7465 基线，**必须按 PTK7452/实际质量重训**。
- **硬件来源**：Juxi B 线 CAD/STL（CERN-OHL-S-2.0）；打印后称重并更新仿真质量。
- **旧内容**：下文 FR-05/06/07/08、7.1/7.2/7.3 的 8 路手动/waypoint/6 维策略是旧骨架参考，不是当前 B 线实现。

---

## 1. 项目概述

### 1.1 背景

参考 SelfRisingRobot 的 2-DOF 慢速起立思路：机器人倒地后，用一条 2 自由度臂（肩关节 + 肘关节）推地，把机身撑回直立。原项目使用 M5Atom + PTK 7465MG + MuJoCo/PPO；本项目改用 **ESP32-S3 + Juxi 6 轴 IMU + PTK 7452MG**（共有 8 个，v0 用 2 个），并采用可维护的自有实现。

### 1.2 目标

1. 用现有器件实现一台 **插电、桌面级、2-DOF 慢速自起立** 样机。
2. 能从 **前/后/左/右 4 种倒地姿态** 自主或半自主起立。
3. 提供手动控制、IMU/舵机标定、状态机、串口日志，便于调试。
4. 为后续接入 RL 策略（MuJoCo/PPO）预留接口，但 **v0 不依赖 RL**。
5. 机械、电气、固件均可复现；BOM 独立维护。

### 1.3 范围

**包含：**

- 2-DOF 臂的机械结构（foot/arm1/arm2/armhorn 或自研等效结构）。
- ESP32-S3 固件：IMU 读取、姿态解算、倒地判定、舵机控制、状态机、标定、串口命令。
- 4 种倒地姿态的 waypoint 起立序列（先手动调，后续可扩展 RL）。
- 插电电源、舵机供电、保护。
- 台架测试、验收标准。

**不包含（v0）：**

- 预防式“倒下前打一下”高速方案。
- 360° 底部转台 / 顶部甩棍方案（另见 research 2.7）。
- 电池、充电、BMS、无线遥控。
- 消费级外壳、玩具认证、量产。
- SelfRisingRobot 的 STL/策略/代码复制（无许可证）。
- 完整 RL 训练流程（v1 可选）。

### 1.4 术语

| 术语 | 说明 |
|---|---|
| 2-DOF 臂 | 两个舵机轴（肩、肘）组成的串联臂，用于推地起立 |
| roll / pitch | 机身横滚/俯仰角；用于判断倒地方向 |
| tilt | 重力方向与机身 Z 轴的夹角；倒地时接近 90° |
| waypoint | 一组两个舵机的目标角；起立序列由多个 waypoint 插值组成 |
| 慢速/中速起立 | B 线每 20ms 目标角变化 ≤0.12 rad；旧骨架 0.08 rad |
| BC / PPO | 行为克隆 / 近端策略优化；B 线用 PPO（可加教师蒸馏） |
| A/B 线 | 本项目的两种舵机路线：A=300° 总线带反馈；B=180° PWM 无反馈 |

---

## 2. 用户与使用场景

| 用户 | 场景 | 需求 |
|---|---|---|
| 开发者/作者 | 桌面调试、参数整定 | 串口命令、实时角度/状态、手动控制、急停 |
| 教育/演示 | 展示“倒地后自己起来” | 一键起立、状态指示、可靠复位 |
| 后续 RL 实验 | 采集/部署策略 | 观测/动作接口、策略 MLP 可替换 |

---

## 3. 系统概述

```
        USB-C 5V                   6V/5A
           │                            │
      ┌────┴─────┐                 ┌────┴─────┐
      │ ESP32-S3 │                 │ 2× PTK   │
      │          │  50Hz PWM       │ 7452MG   │
      │  ┌───────┴─────────────────┴───────┐ │
      │  │ 2R 臂 / 128×128 策略 / 标定      │ │
      │  └───────┬─────────────────────────┘ │
      └────┬─────┘                           │
           │ I²C 0x23 / 100kHz / 3.3V        │
      ┌────┴─────┐                           │
      │ Juxi IMU │                           │
      │ 6 轴     │                           │
      └──────────┘                    共地 ──┘
```

- **机械**：实机为 SelfRisingRobot 3D 打印件 5 件（footP、arm1P、arm2P、armhornP×2）；仿真 `training/b_line/assets/robot_selfrising.xml` 按同一 STL 生成，约 97.4 g。Juxi B 线 CAD 保留为备选。
- **电气**：ESP32-S3 由 USB-C 5V 供电；两个 PTK7452 由独立 **6V/≥5A** 供电；经无源直连转接板；共地。
- 固件：50Hz 控制循环；IMU 读取 50Hz；舵机 50Hz PWM；B 线策略 10 维观测/2 维动作。
- 许可：B 线代码 MIT/Apache；硬件 CAD CERN-OHL-S；见 [licensing.md](licensing.md) 与 [provenance.md](provenance.md)。

---

## 4. 功能需求（FR）

### FR-01 IMU 采集与健康检查

- 使用 Juxi 6 轴 IMU：I²C `0x23`、100kHz、3.3V、11mA。
- 上电等待 ≥5s；读取版本号 `0x01–0x03`；读取欧拉角、加速度、陀螺仪。
- 控制循环内读取失败时记录错误计数；连续失败 ≥500ms 进入 `FAULT` 并收舵机。
- 不读取磁力计/气压计寄存器（6 轴版无）。

### FR-02 姿态解算

- 输出 `roll`、`pitch`、`tilt`、`azimuth`。
- `tilt` 用加速度计计算：`acos(az/|a|)`；`azimuth` 用 `atan2(ay, ax)`。
- `roll/pitch` 仅用于调试/方向分类；**不得只用 Euler 做 >90° 的触发**（万向锁）。
- 支持安装方向修正（符号/offset），至少提供 `AXIS_SIGN`/`AZIMUTH_OFFSET` 配置。

### FR-03 倒地判定与姿态分类

- 倒地：`tilt > 0.75 rad（约 43°）` 持续 `300ms`。
- 分类：根据 roll/pitch 的符号分为 `FRONT/BACK/LEFT/RIGHT` 四类；分类结果决定起立序列。
- 防误触：搬运/手持时角速度大；建议同时要求 `|gyro|` 较低或增加确认时间（可配置）。
- 直立完成：`tilt < 0.25 rad（约 14°）` 持续 `700ms`。

### FR-04 舵机控制

- **B 线 v0 只用 2 路 50Hz PWM**（肩 GPIO4、肘 GPIO5 示例），LEDC **14 位**（ESP32-S3 上限）；转接板为无源直连，不使用 PCA9685。
- 脉宽 500–2500µs，PTK 中位 **1520µs**；`SERVO_US_PER_RAD=636.62`；方向用 `SERVO_SHOULDER_SIGN/ELBOW_SIGN` 校正。
- 目标角每 20ms 最大变化 **0.12 rad**（6 rad/s，B 线策略约定）；`Q_HALF_RANGE=1.55`（±89°）。
- 上电先校准 IMU，再输出 PWM 中位；`s` 停止并保持最后目标，`x` 释放 PWM（卸力），`r` 重新初始化。
- 无位置反馈：固件把指令角/指令角速度当观测；必须保证机械行程无干涉。

### FR-05 手动模式

- B 线当前固件用串口命令：`g` 运行、`s` 停止并保持、`x` 释放 PWM、`r` 重新初始化、`c` 陀螺校准、`t` 关节自检。
- 旧 `sr_support_2dof` 的 `1`–`8` 通道手动/waypoint 保留为调试骨架，不是 B 线主路径。

### FR-06 自动起立状态机

B 线当前是 **hold/run 两态**：

- 上电：IMU 初始化 + 陀螺校准 + PWM 中位，进入 **hold**。
- `g`：进入 **run**，50Hz 运行 10 维策略；`s` 回 hold 并保持最后目标；`x` 释放 PWM；`r` 重新初始化。
- IMU 超过 100ms 无数据：自动 `servo::stop()`（保持最后目标）；持续异常请断电。
- 旧 `BOOT→IDLE→FALLEN_CONFIRM→GETUP→HOLD` 状态机保留在旧骨架，不是 B 线主实现。

### FR-07 Waypoint 起立序列（旧骨架，不是 B 线）

- 旧 `sr_support_2dof` 的 4 姿态 waypoint 仅作为手动调试/备选；B 线用训练好的策略，不需要 waypoint。
- 不要复制 SelfRisingRobot 的 waypoint；本项目 B 线训练不使用它。

### FR-08 完成判定

- B 线策略/评估用：机体 z 轴朝上（`up_z > 0.9`）且躯干高度接近站立高度（±30mm）。
- 旧骨架的 `tilt < 0.25 rad` 仅作调试参考；B 线以策略评估脚本为准。

### FR-09 安全与保护

- 起立总时长 ≤14s；单次堵转 ≤1s（建议 0.5s）。
- 电流检测（INA219 可选）：超过阈值 100ms → 立即停止/收舵机。
- 急停：串口 `x`/按键（可选）立即停止；状态机进入 `ABORT`。
- 电源：5A 保险丝、1000–2200µF、共地；ESP32 不得被舵机拉复位。
- 温度：舵机外壳温度 >60°C 时停止并冷却（人工/可选传感器）。
- 机械：舵机臂/连杆不得夹手；测试时手远离关节扫掠面。

### FR-10 标定与持久化

- IMU：安装方向/符号；可选零偏校准（使用厂商工具/I²C 命令）。
- 舵机：中位、左右端点、offset、脉宽；通过串口/编译常量配置。
- 可选保存到 NVS（Preferences）；v0 可先用编译常量。
- 上电自检：IMU 版本/数据有效、舵机脉宽范围、电源电压（可选）。

### FR-11 日志与调试

- 串口 115200：状态、tilt/roll/pitch、舵机目标、错误计数。
- CSV 输出（10–50Hz）便于 Serial Plotter/Python 分析。
- 可选 Wi-Fi AP + Web UI（v1）：手动/起立/停止/标定。
- 记录每次起立的姿态、耗时、结果、电流（可选）。

### FR-12 启动行为

- 上电：IMU 初始化（0x23/100kHz）→ 陀螺零偏校准（保持静止约 2s）→ PWM 中位 → hold。
- IMU 失败：闪灯/串口报错，不跑策略；检查接线/地址/供电。
- 上电默认 **hold**，发 `g` 才运行策略；`x` 释放 PWM，`r` 重新初始化。
- 不在上电时自动起立。

### FR-13 固件升级/构建

- PlatformIO（推荐）或 Arduino IDE；ESP32-S3 板级支持。
- 不要求 OTA；USB-C 烧录。
- B 线代码结构：`include/config.h`、`include/policy_b.h`、`src/main.cpp`、`src/servo_backend.h`、`src/servo_pwm.cpp`。
- LEDC API 兼容 Arduino-ESP32 2.x/3.x；B 线不使用 SCServo/GPL 库。

### FR-14 RL 策略接口（B 线当前实现）

- 观测（10 维）：`[up_b(3), omega(3), q(2), qdot(2)]`。
- 动作（2 维）：`a ∈ [-1,1]²`，`q_target = a * 1.55 rad`；每 20ms 最多变化 0.12 rad。
- 策略：128×128 Tanh MLP（B 线经验；64×64 覆盖不了四面）。
- 训练/评估/导出：`training/b_line/`；固件：`firmware/sr_support_b_ptk/`。
- 当前 `policy_b.h` 是 PTK7465 基线，最终按 PTK7452/实际质量重训；不使用 SelfRisingRobot 代码/权重/waypoint。

---

## 5. 非功能需求（NFR）

| 编号 | 需求 | 指标 |
|---|---|---|
| NFR-01 | 控制频率 | 50Hz 主循环；IMU 读取 50Hz（可提升到 100Hz）；舵机 PWM 50Hz |
| NFR-02 | 倒地检测延迟 | B 线策略直接以 up/姿态为观测，无单独 300ms 检测；旧骨架 ≤300ms |
| NFR-03 | 起立时间 | 目标 1–10s；评估 episode 8s（400 步 × 20ms） |
| NFR-04 | 起立成功率 | B 线仿真 96% 标称 / 63% DR（PTK7465）；PTK7452 目标先按 8/10 台架 |
| NFR-05 | 舵机目标变化率 | ≤0.12 rad/20ms（B 线） |
| NFR-06 | 电源 | 6V/≥5A；舵机端 1000–2200µF；压降 <0.5V；ESP32 不复位 |
| NFR-07 | 可靠性 | 连续 100 次起立；无扫齿/无复位/温度 <60°C |
| NFR-08 | 代码 | 控制循环无动态分配；I²C 失败可恢复；状态可观测 |
| NFR-09 | 机械 | 2-DOF 臂、±90° 关节、3D 打印 PETG/PLA；可拆装 |
| NFR-10 | 安全 | 急停 <100ms；堵转 ≤1s；保险丝/共地 |

---

## 6. 硬件需求

### 6.1 已有器件

| 器件 | 规格 | 数量 | 备注 |
|---|---|---|---|
| ESP32-S3 开发板 | 3.3V 逻辑、USB-C、5V 输入 | 1 | 具体型号待确认 |
| 舵机转接板 | ESP32-S3 直插；GPIO→3-pin；共用 V+/GND；级联 | 1 | **无源直连，无 PCA9685**；GPIO4–18/CH 映射待口述 |
| Juxi 6 轴 IMU | I²C 0x23、100kHz、3.3V、11mA、5s 启动 | 1 | 无 Mag/BARO |
| PTK 7452MG | 180° PWM、金属齿轮、4.8–7.4V、约 12.2g、25T | **8** | **v0 只用 2 个**；6V 约 3.4 kg·cm，7.4V 约 4.5 |

### 6.2 新增/补齐

见 [../bom/bom.md](../bom/bom.md)。关键项：

- **6V/≥5A 舵机电源**（B 线关键；不是 5V/3A）；7.4V/5A 可选。
- 1000–2200µF、100nF、5A 保险丝、电源开关。
- B 线 3D 打印件（[../hardware/juxi_b_line/STL/](../hardware/juxi_b_line/STL/)）、M2/M3 螺丝/扎带、橡胶 O 圈。
- USB-C 数据线、杜邦线、舵机延长线、IMU 固定。
- 可选 INA219、舵机测试仪、备用舵机。
- 转接板是无源级联；**不要用 ESP32 USB 5V 带两个舵机**。

### 6.3 引脚（B 线示例，待口述/按转接板确认）

> 详见 [pinmap.md](pinmap.md)。B 线只用 2 路 PWM；GPIO4–18 与 CH1–CH8 的实际映射等口述后更新。

| 功能 | ESP32-S3 引脚 | 说明 |
|---|---|---|
| IMU SDA | **GPIO6** | I²C 100kHz；转接板 CH3 信号脚 |
| IMU SCL | **GPIO7** | I²C 100kHz；转接板 CH4 信号脚 |
| IMU VCC | ESP32 3V3 | **不要接 CH3/CH4 的 V+（6V）** |
| IMU GND | CH3/CH4 GND 或 ESP32 GND | 共地 |
| 肩舵机 | GPIO4 | 50Hz PWM；CH1 |
| 肘舵机 | GPIO5 | 50Hz PWM；CH2 |
| 备用 | GPIO15/16/17/18 | CH5–CH8；B 线固件不驱动 |
| LED（可选） | GPIO2 | 状态灯 |
| USB | USB-C | 烧录/供电 |

- 转接板映射：CH1..CH8 = GPIO4、5、6、7、15、16、17、18；CH3/CH4 信号脚借给 IMU。  
- B 线固件不包含 PCA9685 分支；如果转接板实际是 PCA9685，需要另写驱动。
- 如果实际丝印顺序不同，以万用表通断为准，并在 `config.h` 同步修改。
- 避开 GPIO0/3/45/46（strapping）、GPIO19/20（USB）、Flash/PSRAM 占用引脚；以实际板子为准。

### 6.4 电源

- ESP32-S3：USB-C 5V（电脑或 5V/2A 充电头）。
- 舵机：2× PTK7452MG 用独立 **6V/≥5A**；共地；舵机端 1000–2200µF + 100nF + 5A 保险丝。
- 7.4V/5A 可选：接近 4.5 kg·cm，但发热/电流/寿命要实测。
- 如果 8 个舵机同时动作：按每个堵转 2–3A 估算，至少 6V **10A+**；v0 不用。
- 不要用电脑 USB 口直接带舵机；不要用 MB102 面包板电源。
- 电池版（后续）：2S LiPo + 6V/5A BEC；BMS/欠压保护。

---

## 7. 软件架构（B 线）

```
firmware/sr_support_b_ptk/
├─ include/config.h        # 引脚/PTK7452/阈值/策略常量
├─ include/policy_b.h      # 128×128 策略（当前为 PTK7465 基线，需重训）
├─ src/main.cpp            # IMU + Mahony + 50Hz 控制 + 串口
├─ src/servo_backend.h     # 舵机后端接口
└─ src/servo_pwm.cpp       # LEDC PWM（兼容 core 2.x/3.x）
```

训练/导出：

```
training/b_line/
├─ selfright_env.py        # 10 维 obs / 2 维动作 / DR / 多机型
├─ assets/robot_selfrising.xml  # 默认：实机 3D 打印件（脚本生成）
├─ assets/robot_ptk7452.xml     # Juxi 几何（对照）
├─ train.py                # PPO 128×128
├─ evaluate.py             # 标称/DR/逐面
├─ pretrain_teachers.py    # 逐面教师蒸馏（可选）
└─ export_policy.py        # 导出 policy_b.h
```

### 7.1 状态机（B 线）

```
上电 → IMU 初始化/陀螺校准 → PWM 中位 → hold
                                      │ g
                                      ▼
                                    run（50Hz 策略）
                                      │ s / x
                                      ▼
                              hold / released
                                      │ r
                                      ▼
                                  重新初始化
```

- `hold`：不跑策略；`s` 保持最后目标；`x` 释放 PWM。
- `run`：每 20ms 读 IMU、算 Mahony、跑 128×128 策略、限速写 PWM。
- IMU 超过 100ms 无数据：`servo::stop()` 保持最后目标；持续异常请断电。

### 7.2 关键参数（B 线）

| 参数 | 初值 | 备注 |
|---|---|---|
| `POLICY_DT` | 0.02s | 50Hz |
| `CTRL_PERIOD_US` | 20000 | 20ms |
| `MAX_CMD_RATE` | 0.12 rad/step | 6 rad/s |
| `Q_HALF_RANGE` | 1.55 | ±89° |
| `SERVO_CENTER_US` | 1520 | PTK 常见中位 |
| `SERVO_US_PER_RAD` | 636.62 | 2000µs/π |
| `MAHONY_KP/KI` | 6.0 / 0.02 | 姿态融合 |
| 舵机电源 | 6V/≥5A | 7452 约 3.4 kg·cm；7.4V 可选 |

### 7.3 观测/动作接口（B 线）

- 观测（10 维）：`[up_b(3), omega(3), q(2), qdot(2)]`。
- 动作（2 维）：`a ∈ [-1,1]²`，`q_target = a * 1.55`；每 20ms 最多变化 0.12 rad。
- 策略：128×128 Tanh MLP；`training/b_line/export_policy.py` 导出。
- 当前 `policy_b.h` 是 PTK7465 基线；最终按 PTK7452/实际质量重训。

---

## 8. 机械需求

- 2-DOF 串联臂：肩（servo1）+ 肘（servo2）；**实机为 SelfRisingRobot 3D 打印件**（脚座 60×72.9 mm、肩轴高 25.4 mm、肘轴高 70.4 mm、直立总高 168 mm），STL 来源见 [`../docs/provenance.md`](provenance.md)。
- 仿真模型 `training/b_line/assets/robot_selfrising.xml` 由 `tools/build_selfrising_model.py` 从同一 STL 生成；Juxi B 线 CAD 仅作备选（**CERN-OHL-S-2.0**）。
- PTK7452 尺寸 23.6×26.9×11.7 mm，与 PTK7465 基本同壳体；打样前量耳片/出线/舵盘孔距。
- 3D 打印：PETG；0.2mm 层高、4 圈壁、30–40% 填充；按上游打印方向。
- **打印后逐件称重**：仿真按打印件约 51 g、舵机 24.4 g、电控 22 g 建（共 97.4 g）；实测后改 `tools/build_selfrising_model.py` 的 `MASS_*`，重新生成 XML 再训练。
- 机身/脚：末端橡胶 O 圈/皮筋防滑；装配用 M2/M3 + 扎带。
- 不使用 SelfRisingRobot 的代码/权重/waypoint；STL 仅本地仿真实机，不再分发。

---

## 9. 安全需求

- 急停：串口 `x`/按键；≤100ms 停止。
- 堵转：单次 ≤1s；建议 0.5s；电流检测（可选）100ms 切断。
- 起立超时 14s；最多 3 次；失败锁定。
- 电源：保险丝、共地、舵机端电容；禁止热插拔舵机。
- 机械：关节扫掠面内不得放手；舵机臂/连杆无尖角；测试区域清理。
- 固件：I²C 失败/看门狗复位时舵机进入安全姿态（停止 PWM 或回中）。

---

## 10. 测试与验收

### 10.1 单元/台架测试

1. IMU：0x23/100kHz/5s；连续 10min 读取，错误率 <0.1%。
2. 姿态：直立 0°、前/后/左/右 90°；tilt/azimuth 符号正确；>90° 连续。
3. 舵机：0/90/180° 空载；脉宽/offset 标定；5V 压降 <0.5V。
4. 状态机：手动/自动/急停/超时/重试。
5. 电源：两个舵机同时堵转 1s，ESP32 不复位；保险丝不误断。

### 10.2 系统测试

- 4 种倒地姿态各 10 次；成功率 ≥8/10；起立时间 ≤10s。
- 连续 100 次；无扫齿、无复位、舵机温度 <60°C。
- 失败场景：单臂卡住/电源不足/IMU 失效 → 进入 ABORT/FAULT，不无限堵转。
- 机械：臂/脚接触点、重心、关节范围符合设计。

### 10.3 验收标准（v0）

- [ ] IMU 读取稳定；tilt/azimuth 正确；>90° 不跳变。
- [ ] 2 个 PTK 7452MG 可独立/同时控制；标定完成。
- [ ] 手动模式可移动/回中/急停。
- [ ] 4 种姿态至少各 8/10 起立成功；无复位/扫齿。
- [ ] 连续 100 次通过；日志完整。
- [ ] BOM/接线/机械/代码文档齐全。

---

## 11. 里程碑

| 里程碑 | 内容 | 交付 |
|---|---|---|
| M1 | 需求文档评审 | 本文档 v1.0 |
| M2 | 硬件 bring-up | IMU 测试 + 舵机空载 + 电源 |
| M3 | 手动控制/标定 | 串口手动 + offset/脉宽 |
| M4 | 单姿态起立 | 1 组 waypoint 调通 |
| M5 | 4 姿态起立 | 4 组 waypoint + 状态机 |
| M6 | 可靠性 | 100 次 + 安全测试 |
| M7（可选） | RL 策略 | MuJoCo/PPO/MLP 部署 |

---

## 12. 风险与开放问题

| 风险 | 影响 | 对策 |
|---|---|---|
| PTK 7452MG 扭矩/版本差异 | 起不来/扫齿 | 6V 供电；实测；必要时换 7465MG/MG90S；策略重调 |
| 3D 模型/花键不匹配 | 装不上 | 先确认 25T；改 `armhorn`/舵机座；纸板验证 |
| Waypoint 未整定 | 起立失败 | 先单姿态手动调；记录角度；逐步扩展 4 姿态 |
| ESP32-S3 端口差异 | 无法烧录/引脚冲突 | 确认板子 pinout；避开 strapping/USB |
| Juxi IMU 万向锁 | >90° 异常 | tilt/azimuth 用加速度计；roll/pitch 仅调试 |
| 电流/复位 | 起立中断 | 6V/5A、1000–2200µF、共地、保险丝、INA219 |
| B 线 180°/无反馈 | 部分姿态难、卡住不知道 | 128×128 + 教师蒸馏；机械无干涉；急停/断电 |
| PTK7452 比 PTK7465 弱 | 成功率下降 | 6V 按 3.4 kg·cm 重训；或 7.4V 实测；先按 8/10 目标 |
| 打印质量与仿真偏差 | sim2real 失败 | 仿真按 97.4 g 建；打印后逐件称重、改 `MASS_*` 重新生成 XML 再训练；先手扶 |
| 许可/版权 | 商用风险 | B 线代码 MIT/Apache；CAD CERN-OHL-S；B 线固件无 GPL；SelfRisingRobot 不使用 |
| 专利 | 商用风险 | CN109693729A/B 等需 FTO/专利检索 |

**开放问题：**

- PTK 7452MG 实际数量（已确认 8 个）、花键/版本。
- 转接板映射已确认：CH1..CH8 = GPIO4,5,6,7,15,16,17,18；CH3/CH4 信号脚借给 IMU；需核对丝印/级联口顺序。
- 8 个舵机的用途：B 线只用 2 个；如果要用 8 个做多足/其他机构，需要另做机械/固件需求。
- 打印件实际质量/臂长/肩高（需称重测量后写入 `tools/build_selfrising_model.py` 并重新生成 `robot_selfrising.xml`）。
- 6V 还是 7.4V 运行（7.4V 力矩更大但发热/寿命需实测）。
- 是否先做逐面教师蒸馏，还是直接 128×128 从零 PPO。
- 是否加 INA219/按键/OLED（B 线固件默认只用串口）。

---

## 13. 交付物

- 本需求文档（v1.0 评审后）。
- `firmware/sr_support_b_ptk/`：B 线固件（Juxi MIT/Apache + PTK7452 参数）。
- `training/b_line/`：B 线 MuJoCo/PPO 训练、评估、策略导出。
- `hardware/juxi_b_line/`：B 线 CAD/STL/STEP（CERN-OHL-S-2.0）。
- `third_party/juxi-2dof/`：上游许可/NOTICE。
- `docs/b-line.md`、`docs/licensing.md`、`docs/provenance.md`。
- `bom/bom.md` + `bom.csv`（B 线 6V/5A）。
- 测试报告：B 线 4 姿态成功率、100 次可靠性、电源/温度。
- 标定说明：IMU 方向、舵机 1520µs/方向、实际质量/尺寸。

---

## 14. 参考

- Juxi B 线上游：https://github.com/Juxi-Technology/2dof-selfrighting-robot （代码 MIT/Apache；硬件 CERN-OHL-S）
- SelfRisingRobot（无许可证，仅参考方法）：https://github.com/homemadegarbage/SelfRisingRobot
- 作者博客：https://homemadegarbage.com/rl13
- PTK 7452MG 参数页：http://www.ptkhobby.com/pd.jsp?fromColId=104&id=90
- 本项目管理文档：[b-line.md](b-line.md)、[pinmap.md](pinmap.md)、[hardware-validation.md](hardware-validation.md)、[../bom/bom.md](../bom/bom.md)
