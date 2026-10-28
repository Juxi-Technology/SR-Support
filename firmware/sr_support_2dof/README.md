# sr_support_2dof — 旧 8 路/waypoint 骨架（非当前主固件）

> **2026-10-20：当前主方案已改为 B 线**，固件在 [`../sr_support_b_ptk/`](../sr_support_b_ptk/)（PTK7452MG 180° PWM + Juxi B 线）。本目录保留为旧 8 路/PCA9685/waypoint 骨架和手动整定参考，不是当前主固件。

> 需求文档：[../../docs/requirements.md](../../docs/requirements.md)  
> 引脚映射：[../../docs/pinmap.md](../../docs/pinmap.md)  
> 许可/来源说明：[../../docs/licensing.md](../../docs/licensing.md)  
> 状态：**骨架，未编译/未实机验证**（本机没有 ESP32/Arduino C++ 编译环境，只做了静态检查）。`getup_sequence.h` 的 waypoint 目前是占位 `{0,0}`，且 `GETUP_SEQ_READY=0`，固件会拒绝自动起立；机械装好后必须按实测整定。

## 1. 目标

- ESP32-S3 + Juxi 6 轴 IMU + 8 路舵机转接板（v0 只用 CH1/CH2，PTK 7452MG 180° PWM）。
- 支持两种转接板：**LEDC 直连 GPIO** 或 **PCA9685/I²C**。
- 倒地后按 4 种姿态选择 waypoint 序列，慢速推地起立。
- 8 路手动测试、串口调参、急停、超时/重试。
- 可选 v1：加载本项目自训练的 6→64→64→2 MLP 策略（`USE_RL_POLICY`）。

## 2. 文件

| 文件 | 作用 |
|---|---|
| `config.h` | 引脚、8 路舵机、驱动模式、阈值、RL 开关 |
| `state.h` | 主状态机枚举（避免 Arduino 原型生成问题） |
| `i2c_bus.h` | IMU 与 PCA9685 共享 I²C 初始化 |
| `juxi_imu.h` | Juxi 6 轴 IMU 驱动（0x23/100kHz/3.3V；Euler+Accel+Gyro；tilt/azimuth 用加速度计） |
| `servo_driver.h` | `ServoDriver` 抽象 + `LedcServoDriver` + `Pca9685ServoDriver` |
| `servo_pair.h` | `ServoArm`：8 通道目标角、慢速限幅、offset/脉宽、校准 |
| `getup_sequence.h` | 4 种倒地姿态的 waypoint 表（占位，待整定）+ `GETUP_SEQ_READY` |
| `policy_runner.h` | 可选：加载自训练策略（`USE_RL_POLICY=1`） |
| `sr_support_2dof.ino` | 主循环、状态机、串口命令、安全 |

## 3. 接线（示例，按实际板子/转接板确认）

> 你已有 **PTK 7452MG ×8 + ESP32-S3 舵机转接板**；v0 只用 **2 个舵机**。  
> 实际 GPIO/通道映射待口述，见 [../../docs/pinmap.md](../../docs/pinmap.md)。  
> 当前 `config.h` 的示例：I²C=GPIO8/9；舵机 CH1–8=GPIO4/5/6/7/10/11/12/13；按键=GPIO14。

### 3.1 直连 GPIO 模式（`SERVO_DRIVER_MODE 1`）

| 器件 | 引脚 | 接到 | 说明 |
|---|---|---|---|
| Juxi IMU | VCC/3V3 | ESP32-S3 3V3 | 3.3V；不要接 5V |
| Juxi IMU | GND | ESP32-S3 GND | 共地 |
| Juxi IMU | SDA | GPIO8 | I²C 100kHz |
| Juxi IMU | SCL | GPIO9 | I²C 100kHz |
| Servo 1 | 信号 | GPIO4 | 肩关节；50Hz PWM |
| Servo 2 | 信号 | GPIO5 | 肘关节 |
| Servo 3–8 | 信号 | GPIO6/7/10/11/12/13 | 备用 |
| Servo 红 | VCC | 5V/3A 适配器 + | **不要接 ESP32 3V3** |
| Servo 棕 | GND | 适配器 − / ESP32 GND | 共地 |
| 电容 | 2200µF + 100nF | 舵机 5V/GND 就近 | 注意极性 |
| 保险丝 | 2A | 适配器 → 舵机 VCC | 串联 |
| 按键 | 一端 | GPIO14；另一端 GND | 可选，内部上拉 |

### 3.2 PCA9685 模式（`SERVO_DRIVER_MODE 2`）

- ESP32 只接 I²C：SDA=GPIO8、SCL=GPIO9（与 IMU 共用）。
- PCA9685 默认地址 `0x40`；舵机接 CH1–CH8。
- **PCA9685 的 VCC（逻辑电源）接 3.3V**，V+ 用独立 5V/6V 电源，GND 与 ESP32 共地；**不要用 ESP32 USB 5V 带 8 个舵机**。
- 很多 PCA9685 板的 I²C 上拉接到 VCC；如果 VCC=5V，SDA/SCL 会被拉到 5V，可能损坏 ESP32-S3。只能 5V 逻辑的板子要加 I²C 电平转换。
- 如果板子改了地址，改 `config.h` 的 `PCA9685_ADDR`。

> 避开 GPIO0/3/45/46（strapping）、GPIO19/20（USB）、Flash/PSRAM 占用脚。  
> PTK 7452MG 4.8–7.4V；v0 用 5V/3A（2 舵机），扭矩不够可改 6V/3A（ESP32 仍 USB 5V，共地）。  
> 8 个舵机同时动作需要 5V/6V 10A+ 电源。

## 4. 编译/烧录

- Arduino IDE：安装 ESP32 板级支持，选择 ESP32-S3 开发板；打开 `sr_support_2dof.ino`。
- PlatformIO：把本目录作为 `src/` 或 Arduino 项目；依赖 `Wire`（内置）。
- 不需要 M5Atom 库；本固件不依赖 M5Atom。
- Arduino-ESP32 核心 2.x/3.x 的 LEDC API 已兼容；PCA9685 走 `Wire`。
- 默认 `USE_RL_POLICY=0`，不需要 `policy_network.h`。

## 5. 串口命令（115200）

| 命令 | 作用 |
|---|---|
| `g` | 开始起立（waypoint 未整定时会被拒绝） |
| `x` | 急停：停止 PWM，进入 FAULT |
| `r` | 复位：重新初始化 IMU/舵机、回中、进入 IDLE |
| `m` | 手动/自动切换 |
| `p` | 打印状态 |
| `s` | 打印 8 路舵机状态（驱动/角色/目标/当前） |
| `1`–`8` | 选择手动测试通道 |
| `a` / `d` | 选中通道 −/+5° |
| `j` / `l` | 舵机 2（肘）−/+5° |
| `c` | 所有通道慢速回中 |
| `v` | 详细 CSV 输出开关 |
| `?` | 帮助 |

CSV 格式：`state,tilt,roll,pitch,s1_target,s1_current,s2_target,s2_current,attempts,imu_valid`。

配套电脑工具：[`../../tools/sr_tune.py`](../../tools/sr_tune.py)（手动整定/捕获 waypoint）和 [`../../tools/plot_log.py`](../../tools/plot_log.py)（画日志）。

## 6. 状态机

```
BOOT → SELFTEST → IDLE ⇄ MANUAL
                    │ tilt > 43° 且 GETUP_SEQ_READY/RL
                    ▼
             FALLEN_CONFIRM (300ms)
                    │
                    ▼
                 GETUP (waypoints/策略) → HOLD → DONE → IDLE
                    │ timeout/IMU fail
                    ▼
                 ABORT → 冷却/重试（≤3）→ IDLE
```

- 倒地：`tilt > 0.75 rad` 持续 300ms；直立：`tilt < 0.25 rad` 持续 700ms。
- 起立超时 14s；失败冷却 1.5s；最多 3 次。
- IMU 连续 500ms 无数据：运动中 → ABORT；静止 → 2s 后 FAULT。
- 急停：`x`/按钮 → FAULT，需 `r` 复位。
- **安全开关**：`GETUP_SEQ_READY=0` 时 IDLE 不自动起立，`g` 也会被拒绝；防止占位 waypoint 误动作。

## 7. Waypoint 整定（关键）

推荐用电脑工具，不要手改角度：

```bash
pip install -r tools/requirements.txt
python tools/sr_tune.py --port COM5
```

1. **先不装臂/空载**：确认 IMU 0x23/100kHz/5s、串口状态、舵机 0/90/180° 方向。
2. 输入 `m` 进手动；输入 `1`/`2` 选择肩/肘；把机器人摆成一种倒姿。
3. 用 `a/d`（选中通道）或 `j/l`（肘）慢慢移动，观察机身如何被撑起；记录关键角度。
4. 每到关键姿态，输入 `:w` 捕获当前 `s1_target/s2_target`（工具从 CSV 读取并转弧度）。
5. 输入 `:s front`（或 `back/left/right`）生成 `waypoints_front.txt`，粘贴到 `getup_sequence.h`。
6. 最后一个 waypoint 建议 `{0,0}`；长度改 `GETUP_SEQ_LEN`（≤8）。
7. 把 `GETUP_SEQ_READY` 改成 `1`，重新编译；先单姿态跑通，再做另外 3 个。
8. `WAYPOINT_INTERP_MS`（默认 700ms/段）和 `SERVO_TARGET_DELTA_RAD`（0.08）决定速度；先慢后快。

> 不要直接复制 SelfRisingRobot 的 waypoint/STL（无许可证）；自行整定。  
> `GETUP_SEQ_READY=0` 时 `g` 只打印提示，不会动；这是正常的。

## 8. 标定

- **IMU 方向**：倒地方向分类用加速度计推导的 `rollAcc/pitchAcc`（不用 Euler，避免 >90° 万向锁）；向前/后/左/右倒时看 `roll/pitch` 符号；如果分类反了，改 `getup_sequence.h` 的 `POSE_ROLL_SIGN`/`POSE_PITCH_SIGN`。
- **舵机中位/端点**：每路 `SERVO_CENTER_US`、`SERVO_MIN/MAX_US`；PTK 部分型号中位是 **1520µs**，用 `SERVO_OFFSET_US` 加 +20 校正；如果端点顶死/抖动，缩小范围或改 offset。
- **舵机方向**：如果某个舵机转向反了，改 `config.h` 的 `SERVO_SIGN[ch]` 为 `-1.0f`（不要反接电源）。
- **电源**：示波器/万用表看 5V 跌落；两个舵机同时动作不应让 ESP32 复位。
- **PCA9685**：如果 8 路都不动，先查 `0x40` 地址、`OE` 引脚、V+ 电源和共地。

## 9. 安全/限制

- 舵机堵转 ≤1s；起立总时长 ≤14s；急停随时可用。
- 电流检测（INA219）尚未接入；`ServoArm` 只做时间/限位保护。
- 没有电池/充电；插电测试。
- Waypoint 未整定前不要直接上整机；先纸板/空载。
- 这是参考骨架，不是成品；实机测试请戴护目镜/清空关节扫掠面。
- 8 路同时动作前，确认电源/端子/线径能承受 10A+。

## 10. 可选 RL（v1）

- 训练/导出见 [`../../training/README.md`](../../training/README.md)。
- 流程：自建 MuJoCo 模型 → PPO 训练 → 导出 `policy_network.h` → `USE_RL_POLICY=1`。
- 观测顺序：`[rollAcc, pitchAcc, s1, s2, s1_vel, s2_vel]`；动作：目标角增量。
- 不使用 SelfRisingRobot 的代码/权重；详见许可文档。

## 11. 许可

- 本项目代码为独立实现，未复制 SelfRisingRobot（无许可证）的代码/STL/权重/waypoint。
- 根目录 `LICENSE` 当前为 proprietary；如需开源，改成 MIT/Apache-2.0 前先看 [`../../docs/licensing.md`](../../docs/licensing.md)。
- Arduino-ESP32 core 是 LGPL-2.1；闭源商用固件需评估重链接义务（或改用 ESP-IDF，Apache-2.0）。
