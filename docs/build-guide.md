# SR-Support B 线复现手册（客户版）

| 项目 | 内容 |
|---|---|
| 文档版本 | v1.0 |
| 日期 | 2026-10-20 |
| 适用硬件 | ESP32-S3 + Juxi 6 轴 IMU + 无源直连级联转接板 + 2× PTK7452MG（180° PWM） |
| 适用固件 | [`../firmware/sr_support_b_ptk/`](../firmware/sr_support_b_ptk/) |
| 适用训练 | [`../training/b_line/`](../training/b_line/) |
| 当前状态 | B 线代码/文档已整合；**固件已编译并烧录**（PlatformIO 6.2.0 + espressif32 8.0.0，COM27），IMU 尚未接/未识别，训练未实跑、硬件未验证 |
| 上游基线 | Juxi-Technology/2dof-selfrighting-robot `main` @ `6caaf9b`（代码 MIT/Apache；硬件 CERN-OHL-S） |
| 目标 | 让你按本手册从零完成打印、装配、接线、烧录、基线试跑、重训、评估和实机验收 |

> **先读这 5 条**
> 1. 本项目 B 线是 **180° PWM、无位置反馈**；不是 A 线 300° 总线舵机。  
> 2. IMU **只用 I²C**：地址 `0x23`、100 kHz、3.3V、SDA=**GPIO6**、SCL=**GPIO7**；VCC 接 **3V3**（不能用舵机口 V+ 6V）；GND 可走 CH3/CH4 的 GND。不是串口。  
> 3. 舵机电源 **6V/≥5A**；ESP32 用 USB-C 5V 单独供电；两者共地。**不要把 6V 接到 ESP32。**  
> 4. `policy_b.h` 当前是 **PTK7465 基线策略**，只用于接线/台架；最终必须按 PTK7452/实际质量重训。  
> 5. 第一次上电手扶、空载、清空 30 cm；异常立即 `x` 或拔舵机电源。

---

## 0. 当前流程与接口结论

### 0.1 当前流程（从零到复现）

```
开箱验收
  → 打印 B 线 3 个件
  → 舵机 1520µs 回中、装舵盘（臂竖直）
  → 机械装配
  → 接线（IMU I²C + 2 路 PWM + 6V/5A + 共地）
  → 软件环境（PlatformIO + Python）
  → IMU 验证（版本/up 向量/陀螺校准）
  → 舵机与安全验证（t 自检、s/x/r）
  → 基线策略手扶试跑（只验证方向）
  → 称重/量尺寸，更新仿真 XML
  → 训练 128×128（逐面教师+蒸馏 或 从零）
  → 评估（标称/DR/逐面）
  → 导出 policy_b.h，重烧固件
  → 实机 4 姿态 × 10 次 + 100 次可靠性
  → 验收记录
```

### 0.2 IMU：I²C，不是串口

| 项目 | 值 |
|---|---|
| 接口 | **I²C**（固件只实现 I²C） |
| 地址 | `0x23` |
| 时钟 | `100 kHz` |
| 供电 | **3.3V**（接 ESP32 3V3；不要接舵机口 V+ 6V） |
| SDA | **GPIO6**（转接板 CH3 信号脚） |
| SCL | **GPIO7**（转接板 CH4 信号脚） |
| GND | CH3/CH4 的 GND 或 ESP32 GND |
| 上电等待 | **5 s**（`IMU_STARTUP_MS=5000`；旧资料要求） |
| 读取寄存器 | 版本 `0x01–0x03`；加速度 `0x04–0x09`；陀螺 `0x0A–0x0F` |
| 姿态融合 | 固件自己跑 Mahony（`MAHONY_KP=6.0`） |
| 输出率 | 模块出厂可能是 25 Hz；如果实机反应明显滞后，用厂商工具/串口协议设为 100 Hz |

> 模块也支持 UART，但 **B 线固件不使用 UART**。不要同时把 UART 和 I²C 接到同一模块上试图“双路读取”。  
> 旧 Juxi 6 轴模块与 ICM42670P 模块的加速度/陀螺寄存器布局按现有资料一致；首次上电以版本号和 `up` 输出为准。若读数异常，先用 [`../firmware/imu_module_i2c_test/`](../firmware/imu_module_i2c_test/) 对照。

### 0.3 舵机：2 路 50Hz PWM

| 项目 | 值 |
|---|---|
| 型号 | PTK7452MG（180°，金属齿，25T，约 12.2 g） |
| 中位 | **1520 µs** |
| 行程 | 500–2500 µs 约 180° |
| 控制 | 50 Hz，LEDC 14 位（ESP32-S3 上限） |
| 肩信号 | GPIO4（示例，按转接板实际映射改） |
| 肘信号 | GPIO5（示例） |
| 电源 | **6V/≥5A**；7452 约 3.4 kg·cm；7.4V 约 4.5（注意发热） |
| 反馈 | **无**；固件把指令角/指令角速度当观测 |

### 0.4 策略/控制

- 观测 10 维：`[up_b(3), omega(3), q(2), qdot(2)]`。
- 动作 2 维：`q_target = action × 1.55 rad`；每 20 ms 最多变化 **0.12 rad**。
- 网络：128×128 Tanh MLP（B 线经验；64×64 覆盖不了四面）。
- 控制频率：50 Hz；IMU 读取 50 Hz（loop 里更快读取，控制步 20 ms）。

---

## 1. 系统总览

```
            USB-C 5V                        6V/≥5A
               │                              │
        ┌──────┴──────┐                ┌──────┴──────┐
        │  ESP32-S3   │                │ 保险丝/开关  │
        │             │                │ 1000–2200µF │
        │  GPIO6/7 ───┼── I²C ──┐      └──────┬──────┘
        │  GPIO4/5 ───┼── PWM ──┼───────┐     │
        └─────────────┘         │       │     │
                                │   ┌───┴─────┴───┐
                          ┌─────┴───┤ 无源级联转接板 │
                          │ Juxi IMU│ CH1  CH2 ... │
                          │ 0x23    └──┬──────┬────┘
                          └─────────────┤      │
                                       肩舵机  肘舵机
                                       共地 ───┘
```

- ESP32 只负责：I²C 读 IMU、50Hz 跑策略、两路 PWM。
- 转接板只负责：把 GPIO 引到 3-pin 排针、把 6V 分配到各舵机口、级联。
- **没有 PCA9685、没有 GPIO 扩展、没有舵机位置反馈。**

---

## 2. 物料与工具

### 2.1 已有（本项目假设）

| 物料 | 数量 | 检查点 |
|---|---:|---|
| PTK7452MG | 8 | v0 只用 2 个；确认 25T、1520 µs、尺寸 23.6×26.9×11.7 mm |
| ESP32-S3-DevKitC-1 或兼容板 | 1 | USB-C 能识别；GPIO4/5/6/7/15/16/17/18 可用 |
| 无源直连级联转接板 | 1 | 每口信号独立；V+/GND 共用；无 PCA9685 |
| Juxi 6 轴 IMU | 1 | I²C 0x23、3.3V、6 轴（无 Mag/BARO） |

### 2.2 必买/补齐

| 物料 | 规格 | 数量 | 用途 |
|---|---|---:|---|
| 6V/5A 电源适配器 | DC 5.5/2.1 或端子 | 1 | 两个 PTK7452 |
| 电解电容 | 1000–2200 µF/10V | 1 | 舵机电源端 |
| 陶瓷电容 | 100 nF | 1 | 舵机电源端 |
| 自恢复保险丝 | 5 A | 1–2 | 舵机支路 |
| 电源开关 | 6V/5A | 1 | 断电 |
| USB-C 数据线 | 支持数据 | 1 | 烧录/串口 |
| 5V/2A USB 充电头 | — | 1 | ESP32 独立供电 |
| 杜邦线/排线 | 母对母/公对母 | 1 套 | I²C + 信号 |
| 舵机延长线 | 10–20 cm | 2 | 走线 |
| M2/M3 螺丝 + 扎带 | — | 1 套 | 装配 |
| 橡胶 O 圈/皮筋 | — | 1 套 | 末端垫防滑 |
| VHB/双面胶 | — | 1 | 固定 IMU |
| PETG 线材/打印服务 | 1.75 mm | 1 卷/1 套 | B 线打印件 |

### 2.3 工具

- 3D 打印机或打印服务；
- 万用表（通断/电压/电流）；
- 十字螺丝刀、内六角、剪线钳/剥线钳；
- 热缩管/绝缘胶带；
- 卡尺（量舵机/臂长/肩高）；
- 电子秤（1 g 精度，打印后称重）；
- 电脑（Windows 10/11）、USB-C 数据线；
- 可选：舵机测试仪、INA219、示波器。

---

## 3. 阶段 0：开箱与转接板验收（必须先做）

### 3.1 舵机检查

- [ ] 型号是 **PTK7452MG**，不是 SG90/MG90S。
- [ ] 尺寸：23.6×26.9×11.7 mm（卡尺量）。
- [ ] 输出花键 **25T**；舵盘能装上，螺丝孔对齐。
- [ ] 手动转舵盘：无卡滞、无扫齿声。
- [ ] 记录两个舵机的编号/外观（后续区分肩/肘）。

### 3.2 IMU 检查

- [ ] 模块是 6 轴（无 Mag/BARO）。
- [ ] 载板丝印/资料确认 I²C 0x23、3.3V。
- [ ] 用万用表测 VCC-GND 不短路。
- [ ] 记录模块印字方向（+X/+Y/+Z）。

### 3.3 转接板连续性测试（关键 STOP/GO）

断电，用万用表通断档：

- [ ] 每个 3-pin 舵机口的 **V+ 是共通的**。
- [ ] 每个口的 **GND 是共通的**。
- [ ] 每个口的 **信号脚彼此不短路**。
- [ ] 信号脚与 V+/GND 不短路。
- [ ] 从每个信号脚找到对应的 ESP32 GPIO（蜂鸣/通断），记录到 [`pinmap.md`](pinmap.md)。
- [ ] 按你的板子记录：CH1..CH8 = GPIO4,5,6,7,15,16,17,18；CH3/CH4 信号脚将用于 IMU SDA/SCL。
- [ ] 用电阻档测 CH3/CH4 信号对 V+、对 GND：应为高阻；如果有 <10k 到 V+ 的上拉/串阻，不要用这两个口做 I²C。
- [ ] 确认 CH3/CH4 的 V+ 与信号脚不短路；IMU 的 VCC 不会接到这两个 V+。
- [ ] 确认板上没有 PCA9685/移位寄存器；如果有一个芯片，拍型号给我。
- [ ] 如果 V+ 经过稳压器：测输入/输出关系，确认 6V 输入是否安全；不确定就先不要接 6V。
- [ ] 如果 V+ 会反灌到 ESP32 的 5V 脚：**不要连接**；ESP32 只用 USB 供电。

> **STOP**：如果所有信号脚是并联的，B 线无法独立控制肩/肘。需要改板/飞线，或换一块每口信号独立的转接板。  
> **STOP**：如果 V+ 与 GND 短路、或 V+ 电压不是预期的 6V，先排查，不要接舵机。

### 3.4 记录

把以下内容填进 [`pinmap.md`](pinmap.md)：

| 项目 | 实测 |
|---|---|
| 板子通道顺序 | CH1..CH8 = GPIO4,5,6,7,15,16,17,18（待丝印核对） |
| CH1 信号 → GPIO | |
| CH2 信号 → GPIO | |
| CH3 信号 → GPIO | |
| CH4 信号 → GPIO | |
| V+ 来源/电压 | |
| 是否有稳压/芯片 | |
| 级联口顺序 | |

---

## 4. 阶段 1：3D 打印

### 4.1 文件

当前实机是 **SelfRisingRobot 3D 打印件**，在你本地目录：

`D:\Project\3D-Models\self-rising-robot\source\`

| 文件 | 数量 | 说明 |
|---|---:|---|
| `footP.stl` | 1 | 底座：底板 + 肩舵机塔 + 转轴销 |
| `arm1P.stl` | 1 | 一级摆臂（Z 形曲柄），带肘舵机座 |
| `arm2P.stl` | 1 | 二级长摆臂 |
| `armhornP.stl` | **2** | 舵机摇臂片，`arm1P`、`arm2P` 各一片 |

- PTK7452 的安装孔距是 **30.8 mm（中间孔排）**，原打印件是 27.8 mm；改配件在 `output/modified/footP_7452.stl`、`arm1P_7452.stl`（补孔 + 凸台），要实机锁螺丝就用改配件。
- 这些 STL **没有许可证**：只用于你自己的实机，不要上传/分发；本项目仿真用的副本在 `training/b_line/assets/selfrising/`（同样不分发）。
- Juxi B 线 STL（`hardware/juxi_b_line/STL/`）保留为备选结构，不是当前实机。

### 4.2 参数

- 材料：**PETG**（PLA 也能用但脆）。
- 层高 0.2 mm；4 圈壁；30–40% 填充。
- 按 STL 原始姿态摆放；`footP` 底板贴床，`arm1P`/`arm2P` 侧躺，`armhornP` 平放。
- 悬垂/舵机座内部开树状支撑；拆支撑后修孔口。

### 4.3 打印后检查

- [ ] 四个件无翘边/层裂。
- [ ] Ø5.0 销能穿进 Ø5.4 孔，转动顺滑（0.4 mm 间隙）。
- [ ] 舵机放进座里不强行挤压；PTK7452 耳片孔对得上（原孔 27.8 mm 对不上 30.8 mm 时用改配件）。
- [ ] 摇臂片 2×M2 孔与打印件底孔对齐；Ø2/Ø6.2 孔与关节轴线同轴。
- [ ] 一级臂/二级臂不碰底座/舵机。
- [ ] 逐件称重并记录（见阶段 8）。

---

## 5. 阶段 2：机械装配

### 5.1 舵机回中（1520 µs）

B 线固件启动后会输出 1520 µs，但它同时需要 IMU；为了先装舵盘，用专用中位 sketch：

1. 只接两个舵机的 **信号线** 到 GPIO4/5，接好 6V 电源和共地。
2. 烧 [`../firmware/servo_center_ptk/servo_center_ptk.ino`](../firmware/servo_center_ptk/servo_center_ptk.ino)。  
   Arduino IDE：开发板选 **ESP32S3 Dev Module**；如果用板上的 USB 口看串口，**USB CDC On Boot = Enabled**；Flash Size 按板子（DevKitC-1 通常 8MB）；其他默认。
3. 串口 115200，应看到：
   ```
   PTK7452 center helper
   CH1(shoulder)=1520us  CH2(elbow)=1520us  selected=CH1
   ```
4. 两个舵机都输出 1520 µs；装舵盘时让 **大臂、小臂都竖直向上**。
5. 如果舵盘中位偏了，可用 `1/2` 选通道，`+/-` 每次 10 µs 微调（范围 1400–1640），记下最终值；后续把偏移写进固件 `SERVO_CENTER_US` 或重装舵盘。

> 装舵盘前先断电；装好后手转关节，确认不碰结构。  
> 已烧 B 线固件时，也可以不重烧、直接用 [`../tools/servo_center.py`](../tools/servo_center.py) 发送 `r` 回中：  
> `.venv-pio/Scripts/python.exe tools/servo_center.py --port COM27`（回中到 1520 µs，固件进入 hold）。
> 不要用“反接电源”改方向；方向用固件 `SERVO_*_SIGN`。

### 5.2 装配顺序

按你的实际结构（底座 → 肩舵机 → 一级臂 → 肘舵机 → 二级臂 → 末端）：

1. **肩舵机**（GPIO4）放进 `footP` 的塔座，输出轴沿 **−X**，轴心对准关节 A（Y −79 / Z 99.6 mm）；用 M2×16 + 凸台/改配件固定。
2. **摇臂片 ①** 用 2×M2 固定在 `arm1P` 的 −X 端面；Ø2/Ø6.2 孔对准关节 A，舵盘通过 Ø2 螺丝与摇臂片连接。
3. `arm1P` 的 Ø5.4 轴套套进 `footP` 的 Ø5.0 销；手转确认绕 **X** 轴自由。
4. **肘舵机**（GPIO5）装进 `arm1P` 顶部座，输出轴沿 **−Y**，轴心对准关节 B（X −141.9 / Z 144.6 mm）。
5. **摇臂片 ②** 用 2×M2 固定在 `arm2P` 横杆的 −Y 端面；Ø2/Ø6.2 孔对准关节 B。
6. `arm2P` 的 Ø5.4 孔套进 `arm1P` 的 Ø5.0 销；手转确认绕 **Y** 轴自由。
7. 二级臂末端贴橡胶/防滑垫（原设计无专用垫，可缠自硫化胶带或热缩管）。
8. ESP32-S3 + 转接板 + IMU 放在 `footP` 底板上；IMU 刚性固定，印字 +X 朝前、+Z 朝上（以实际安装方向为准，固件可改符号）。
9. 线缆走底板边缘，留出两级臂的扫掠空间。

> 关节 A/B 的坐标来自 `data/assembly.json`（装配坐标系，mm）；仿真模型已按同一坐标生成，装配时用卡尺复核肩轴高 25.4 mm、肘轴高 70.4 mm（相对底板底面）。

### 5.3 装配后检查

- [ ] 两关节全程手动转动无卡滞。
- [ ] 大臂/小臂不碰底座/塔/线缆。
- [ ] 末端垫位置与 CAD 一致。
- [ ] 舵盘螺丝拧紧但不过度压舵机。
- [ ] IMU 固定牢，不会随线晃动。

**STOP**：任何干涉都必须先修结构，不要靠“策略会避开”来赌。

---

## 6. 阶段 3：电气接线

### 6.1 接线表（示例）

**转接板通道映射（按你提供的顺序）**

| 通道 | GPIO | B 线用途 |
|---|---|---|
| CH1 | GPIO4 | 肩舵机信号 |
| CH2 | GPIO5 | 肘舵机信号 |
| CH3 | GPIO6 | **IMU SDA**（信号脚） |
| CH4 | GPIO7 | **IMU SCL**（信号脚） |
| CH5 | GPIO15 | 备用 |
| CH6 | GPIO16 | 备用 |
| CH7 | GPIO17 | 备用 |
| CH8 | GPIO18 | 备用 |

**接线**

| 器件 | 引脚 | 接到 | 说明 |
|---|---|---|---|
| IMU | VCC | ESP32 **3V3** | 3.3V；**不要接舵机口 V+ 6V** |
| IMU | GND | CH3/CH4 的 GND 或 ESP32 GND | 共地 |
| IMU | SDA | GPIO6（CH3 信号脚） | I²C 100 kHz |
| IMU | SCL | GPIO7（CH4 信号脚） | I²C 100 kHz |
| 肩舵机 | 信号 | GPIO4（CH1） | 50Hz PWM |
| 肘舵机 | 信号 | GPIO5（CH2） | 50Hz PWM |
| LED | 可选 | GPIO2 | 状态灯 |
| 舵机 | 红 V+ | 6V/5A 电源 +（经保险丝/开关） | **不要接 ESP32** |
| 舵机 | 棕/黑 GND | 电源 − / ESP32 GND | 共地 |
| 电容 | 1000–2200 µF | 舵机 V+/GND 就近 | 注意极性 |
| 保险丝 | 5A | 电源 → 转接板 V+ | 串联 |

> CH3/CH4 只借用 **信号 + GND**；这两个口的 **V+ 悬空不接**。IMU 的 VCC 必须来自 ESP32 3V3（或确认过的 3.3V 源）。  
> **不要**把 IMU 的 4-pin 排线直接插到 3-pin 舵机口：针数/顺序不同，VCC 可能接到 6V 而烧模块。必须逐根接线、逐根核对。  
> I²C 线尽量短（<20 cm），SDA/SCL 与 GND 成对走；模块通常自带 4.7k 上拉到 3.3V；若没有，自己加 4.7k 到 3.3V。**不要上拉到 6V。**  
> 如果转接板丝印顺序不是 CH1..CH8=GPIO4,5,6,7,15,16,17,18，以万用表通断为准，并同步改 `config.h`。

### 6.2 电源链

```
6V/5A 适配器 + → 5A 保险丝 → 电源开关 → 转接板 V+
6V/5A 适配器 − → 转接板 GND → ESP32 GND（共地）
ESP32 → USB-C 5V（独立）
```

- **不要把 6V 接到 ESP32 的 5V/3V3/USB。**
- 电容正极接 V+，负极接 GND；反接会爆。
- 舵机线色序：常见 橙/红/棕 = 信号/V+/GND；以实物为准。
- 级联排针每个口的 V+/GND/信号顺序要一致；插反会烧。

### 6.3 首次上电（不接舵机）

1. 只接 6V 电源和万用表，不接舵机。
2. 测转接板 V+ 对 GND：应为 6V 左右；极性正确。
3. 测 ESP32 3V3 对 GND：3.3V；USB 供电正常。
4. 接一个舵机，测空载电流/电压；再`t`自检（需要固件，见阶段 5/6）。
5. 接第二个舵机，重复。

**STOP**：V+ 高于 6.5V、极性反、或一接舵机 ESP32 就复位 → 先查电源/共地/电容。

---

## 7. 阶段 4：软件环境

### 7.1 Python（训练/评估/导出）

在仓库根目录 `D:\Project\SR-Support`：

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r training/b_line/requirements.txt
```

检查：

```bash
python -c "import mujoco, gymnasium, stable_baselines3, torch; print('ok')"
```

### 7.2 PlatformIO（固件烧录）——不用 ESP-IDF

> 本机已安装：PlatformIO Core **6.2.0** + VS Code 扩展；B 线固件已编译通过（espressif32 8.0.0 / Arduino core 3.3.12，RAM 7.6%，Flash 13.0%）。详见 [`platformio-install.md`](platformio-install.md)。

**结论：主固件用 PlatformIO（Arduino framework），不是 ESP-IDF。**  
底层烧录器是 `esptool`，由 PlatformIO 自动调用；你不需要安装 ESP-IDF，也不需要 `idf.py`。

方式 A：VS Code（推荐）

1. 安装 VS Code。
2. 扩展商店安装 **PlatformIO IDE**。
3. `File → Open Folder` 打开 `firmware/sr_support_b_ptk`。
4. 左下角选择环境 **ptk7452**。
5. 点 **Upload**（箭头图标）；首次会下载 espressif32/Arduino core，时间较长。
6. 点 **Monitor**（插头图标），波特率 115200。

方式 B：命令行

```bash
pip install platformio
pio --version
pio device list
```

> 本机已把 PlatformIO 装在项目内 `.venv-pio`，`pio` 默认不在 PATH。你可以先激活：
> ```bash
> source .venv-pio/Scripts/activate
> ```
> 或直接用完整路径：
> ```bash
> .venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload
> ```

```bash
pio run -d firmware/sr_support_b_ptk -t upload
```

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM5
```

> **如果串口反复刷 `IMU not found`/`ms...`**：多半是 USB-UART 的 DTR/RTS 在自动复位。用上面的 `--rts 0 --dtr 0`。本机 COM27 实测这样才稳定。  
> **串口无输出时**：如果你用 ESP32-S3 板上的 USB 口（不是 UART 口），Arduino IDE 里把 **USB CDC On Boot** 设为 **Enabled**；PlatformIO 可加 `-DARDUINO_USB_CDC_ON_BOOT=1 -DARDUINO_USB_MODE=1` 后重编译。  
> 首次构建记录 PlatformIO 解析到的 `espressif32` 版本（`pio system info`）。  
> 本固件的 LEDC 代码兼容 Arduino-ESP32 2.x/3.x；如果编译报 `ledcAttach`/`ledcSetup`，把报错发我。

### 7.3 Windows 注意事项

- 训练默认用 `DummyVecEnv`（顺序执行），避免 Windows 多进程 pickle 问题；`--n-envs` 建议 2–4。
- 串口是 `COMx`；`pio device list` 查看。
- 如果 COM 口不出现：换支持数据的 USB-C 线、装 CP210x/CH340 驱动、按 BOOT 再上电。

---

## 8. 阶段 5：IMU 单模块验证（I²C）

### 8.1 接线

只接 IMU：

- VCC → 3V3
- GND → CH3/CH4 的 GND 或 ESP32 GND
- SDA → GPIO6（CH3 信号脚）
- SCL → GPIO7（CH4 信号脚）

> CH3/CH4 的 V+ 悬空；不要把 6V 接到 IMU。
> **IMU VCC 必须接 3V3，不是 5V5、更不是 6V。** 接 5V 可能让模块不亮或损坏；如果已经接错，先断电改 3V3，再测。
> **本机实测：经转接板 CH3/CH4 信号不稳定（版本号乱跳/偶发 0x00）；IMU SDA/SCL 直接接 ESP32 GPIO6/7 后稳定。** 优先直连；固件已改为 IMU 初始化最多重试 10s。

舵机电源可以先不接；ESP32 只接 USB。

### 8.2 烧 B 线固件

```bash
pio run -d firmware/sr_support_b_ptk -t upload
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM5
```

> 如果日志只有 `IMU not found; check wiring/address 0x23`，说明 ESP32 和固件正常，但 IMU 没接/没接对。先按 8.1 接线；还不行就烧 [`../firmware/i2c_scanner/`](../firmware/i2c_scanner/) 扫地址，确认是不是 `0x23`。

### 8.3 预期启动日志（代码逻辑，未实机验证）

```
waiting for IMU startup 5000 ms...
IMU version x.y.z
Calibrating gyro: keep the robot still
gyro bias (rad/s): ...
servo start q: 0.00 0.00 rad
ready; send g to run
```

- 保持静止约 2 s 完成陀螺校准。
- 每 250 ms 输出：
  ```
  up +0.00 +0.00 +1.00 | w ... | q +0.00 +0.00 | qd ... | hold
  ```
- 直立时 `up` 应接近 `(0,0,1)`；倾斜时对应分量变化。

### 8.4 方向/轴检查

- 模块印字 +X 朝前、+Y 朝左、+Z 朝上。
- 如果 `up` 不对：检查安装方向；或在 `main.cpp` 的 `raw_to_si()`（搜索 `IMU AXES`）交换/取反轴。
- 如果 `IMU not found`：
  - 3.3V 是否正常；
  - SDA/SCL 是否接反；
  - 地址是否 0x23（用 I²C 扫描）；
  - 100 kHz；
  - 共地；
  - 5 s 启动等待是否足够；
  - 模块是否 6 轴版本。
- 如果数据明显滞后：模块出厂 ODR 可能是 25 Hz；用厂商工具/串口协议设为 100 Hz。

### 8.5 验收

- [ ] 版本号可读；
- [ ] 陀螺校准成功；
- [ ] 直立 `up ≈ (0,0,1)`；
- [ ] 前后/左右倾斜符号正确；
- [ ] 无 I²C 掉线。

---

## 9. 阶段 6：舵机与安全验证

### 9.1 上电顺序

1. 手扶机器人，手臂大致竖直。
2. 先只接 ESP32 USB，确认 IMU/启动日志。
3. 再给舵机 6V 上电。
4. 固件会输出 1520 µs 中位；手臂应保持竖直（不跳）。

### 9.2 `t` 自检

串口发 `t`：

```
self-test: +0.5, -0.5, neutral (0.9 s each)
self-test done; hold
```

- 肩 q>0 应让手臂向 **−Y（右侧）** 倒；
- 肘 q>0 应让小臂向 **+X（前方）** 弯。
- 如果方向反：改 `SERVO_SHOULDER_SIGN`/`SERVO_ELBOW_SIGN`，或重装舵盘；不要反接电源。

### 9.3 安全命令

| 命令 | 行为 | 注意 |
|---|---|---|
| `s` | 停止策略，PWM 保持最后目标 | 仍有力矩，堵转请 `x`/断电 |
| `x` | detach PWM，舵机卸力 | 手臂会因重力落下；先扶住 |
| `r` | 重新初始化 PWM、回中位 | `x` 后必须 `r` 才能再 `g` |
| `g` | 运行策略 | 上电默认 hold |

### 9.4 电流/温度

- 6V 空载/动作电压跌落 <0.5V；ESP32 不复位。
- 单次堵转 ≤1s；外壳温度 >60°C 停止冷却。
- 如果舵机嗡嗡响/发热：中位偏、机械干涉、力矩不足；先修机械。

### 9.5 验收

- [ ] `t` 两个关节方向正确；
- [ ] `s` 保持、`x` 卸力、`r` 回中；
- [ ] 无异常电流/复位/发热；
- [ ] 手动全程无干涉。

---

## 10. 阶段 7：基线策略试跑（只验证方向）

> `policy_b.h` 是 Juxi 的 **PTK7465 128×128 基线**，不是 PTK7452 最终策略。  
> 这一步只确认“接线/方向/机械不卡”，不要用它判断成功率。

1. 手扶机器人，摆成一种倒地姿态（roll 或 pitch ±90°），手臂大致朝上。
2. 周围 30 cm 清空，手放在电源开关/舵机电源旁。
3. 发 `g`。
4. 观察手臂是否朝“撑地”方向动；一有异常立即 `x` 或拔舵机电源。
5. 如果方向明显反/越推越倒：立即停，回到阶段 6 检查符号/IMU 轴。
6. 记录：是否能动、方向、是否卡住、是否复位。

### 验收

- [ ] 手臂能动且方向合理；
- [ ] 无卡死/扫齿/复位；
- [ ] 知道 `x` 和断电位置；
- [ ] 不要求站起来（基线策略不保证 PTK7452）。

---

## 11. 阶段 8：称重、量尺寸、更新仿真

### 11.1 测量表

| 项目 | 实测 | 仿真当前值 |
|---|---:|---:|
| 整机质量 | ____ g | **97.4 g** |
| footP（底座） | ____ g | 17.8 g |
| arm1P（一级臂） | ____ g | 9.7 g |
| arm2P（二级臂） | ____ g | 20.0 g |
| armhornP ×2 | ____ g | 1.75 g ×2 |
| PTK7452MG ×2 | ____ g | 12.2 g ×2 |
| 电控（ESP32-S3+转接板+IMU+线材） | ____ g | 22 g（盒 52×26×18 mm） |
| 脚座尺寸 | ____ mm | 60 × 72.9 mm |
| 肩轴高（底面→肩轴） | ____ mm | 25.4 mm |
| 肘轴高 | ____ mm | 70.4 mm |
| 直立总高（含二级臂） | ____ mm | 168 mm |

### 11.2 更新仿真模型

> 不要手改 XML。模型由脚本生成：

1. 改 `tools/build_selfrising_model.py` 顶部的 `MASS_*`（和需要的电控盒尺寸/位置）。
2. 重新生成模型：

```bash
.venv/Scripts/python.exe tools/build_selfrising_model.py
```

3. 生成后先跑 `--smoke`，确认 XML 能加载、整机质量打印值和实测一致。
4. 记录本次修改（日期/质量/尺寸）到 [provenance.md](provenance.md)。

> 不做这一步，仿真成功率和实机没有对应关系。

---

## 12. 阶段 9：训练

### 12.1 冒烟测试

```bash
python -m training.b_line.train --robot selfrising --smoke --n-envs 2
```

- 只跑少量步数，确认 MuJoCo/SB3/XML/路径都正常。
- 看到 `saved training/b_line/models/ppo_selfrising/final.zip` 即通过。
- 本机实测（2026-10-22）：MuJoCo 3.16.0 + SB3 2.9.0 + PyTorch 2.14.1 CPU，**40,960 步约 28 s，1428 fps**。
- 看 MuJoCo 窗口：`python -m training.b_line.play --random --episodes 1`（本机已验证窗口能打开并跑完 400 步）。

> `n_steps=1024`、`batch_size=2048`，所以 `--n-envs` 至少 2；建议 4。

### 12.2 方案 A：128×128 从零训练

```bash
python -m training.b_line.train --robot selfrising --steps 3000000 --n-envs 4 --hidden 128
```

- CPU 训练，数小时；建议整夜跑。
- Windows 用 DummyVecEnv，8 env 可能更慢；4 个先跑通。
- 显存/内存不足：减 `--n-envs`、减 `--steps`。

### 12.3 方案 B：逐面教师 + 蒸馏（更接近 Juxi B 线配方）

先训练 4 个单面教师（单行命令，Windows 也可用）：

```bash
python -m training.b_line.train --robot selfrising --poses roll_pos --run-name ppo_selfrising_roll_pos --hidden 128 --steps 2000000
```

```bash
python -m training.b_line.train --robot selfrising --poses roll_neg --run-name ppo_selfrising_roll_neg --hidden 128 --steps 2000000
```

```bash
python -m training.b_line.train --robot selfrising --poses pitch_pos --run-name ppo_selfrising_pitch_pos --hidden 128 --steps 2000000
```

```bash
python -m training.b_line.train --robot selfrising --poses pitch_neg --run-name ppo_selfrising_pitch_neg --hidden 128 --steps 2000000
```

蒸馏 + PPO：

```bash
python -m training.b_line.pretrain_teachers --robot selfrising --hidden 128 --steps 2000000 --teachers roll_pos=training/b_line/models/ppo_selfrising_roll_pos/final.zip,roll_neg=training/b_line/models/ppo_selfrising_roll_neg/final.zip,pitch_pos=training/b_line/models/ppo_selfrising_pitch_pos/final.zip,pitch_neg=training/b_line/models/ppo_selfrising_pitch_neg/final.zip
```

- 教师必须在同一 XML/同一 `q_half`/同一观测下训练。
- 不使用 SelfRisingRobot 的 waypoint；教师从零 PPO。
- 如果某面教师成功率低，先加步数/调奖励/检查该面几何，再做蒸馏。

### 12.4 训练验收

- [ ] 训练完成、模型保存；
- [ ] 训练日志无 NaN/崩溃；
- [ ] 评估标称成功率达到你设定的门槛（见阶段 10）；
- [ ] 记录训练命令、seed、步数、XML 版本。

---

## 13. 阶段 10：评估

### 13.1 命令

标称：

```bash
python -m training.b_line.evaluate --robot selfrising --episodes 100
```

DR + 逐面：

```bash
python -m training.b_line.evaluate --robot selfrising --episodes 100 --dr --per-face --home
```

结果写入 `training/b_line/models/eval_selfrising_*.json`。

### 13.2 成功定义

- 策略 `info["upright"]`：`up_z > 0.90` 且脚座高度在站立高度 ±30 mm（只要求扶正）。
- 最终竖直姿态由 `StandHomer` 微调：`up_z>0.95` 连续 10 个控制周期（0.2 s）后，以 **0.12 rad/step** 把目标角归零并保持；`up_z<0.95` 暂停收臂，`up_z<0.90` 交回策略。v2 策略在起立过程中已把手臂带到 q≈0.1–0.35，微调只需 0.06–0.10 s。
- `--home` 评估要求 episode 最后 25 步（0.5 s）中 ≥90% 满足：
  - `up_z > 0.90`；
  - 脚座高度 ±30 mm；
  - **两个关节指令角 `|q| < 0.12 rad`（手臂竖直向上）**。
- 只把机身扶正、手臂横着不算最终成功；最终姿态就是装配姿态（手臂竖直）。
- `t_stand`：从某一时刻起直到结束都直立的最早时间。

### 13.3 验收门槛（建议）

| 阶段 | 门槛 |
|---|---|
| 标称随机倒地 | ≥80%（先跑通；Juxi B 线参考 96%） |
| DR 随机倒地 | ≥50%（Juxi B 线参考 63%；PTK7452 可能更低） |
| 四姿态逐面 | 每面 ≥70% 起步，最终目标 ≥80% |
| 实机 | 每面 ≥8/10；100 次无硬件损坏 |

> 不要直接用 Juxi 的 96% 作为你的验收线；那是 PTK7465 + 他们的几何/质量。

---

## 14. 阶段 11：导出策略并重烧

```bash
python -m training.b_line.export_policy --robot selfrising
```

- 默认覆盖 `firmware/sr_support_b_ptk/include/policy_b.h`。
- 可选 C/PyTorch 校验（需要本机 `clang`）：

```bash
python -m training.b_line.export_policy --robot selfrising --verify
```

- 重新编译/烧录：

```bash
pio run -d firmware/sr_support_b_ptk -t upload
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM5
```

- 上电仍是 hold；`g` 才跑新策略。
- 固件已内置站立收臂状态机（2026-10-22）：`up_z>0.95` 连续 10 个控制周期（0.2 s）→ 目标角以 0.12 rad/20 ms 归零并保持；`up_z<0.95` 暂停，`<0.90` 交回策略。
- 如果编译报 `POLICY_OBS_DIM`/`POLICY_ACT_DIM` 不匹配：检查导出的 header 是否是 10→128→128→2。

---

## 15. 阶段 12：实机验收

### 15.1 单姿态 10 次

1. 手扶摆成 `roll_pos`，放手前发 `g`，记录成功/时间。
2. 重复 10 次；每次失败记录原因（卡住/方向/力矩/滑）。
3. 换 `roll_neg`、`pitch_pos`、`pitch_neg`，各 10 次。

记录表：

| 姿态 | 成功/10 | 平均时间 | 失败原因 | 电流峰值 | 最高温度 |
|---|---:|---:|---|---:|---:|
| roll_pos | | | | | |
| roll_neg | | | | | |
| pitch_pos | | | | | |
| pitch_neg | | | | | |

### 15.2 100 次可靠性

- 混合四姿态，连续 100 次；每 10 次检查：
  - 舵机温度、齿轮声、舵盘螺丝、线缆；
  - 电源/电容温度；
  - 结构裂纹。
- 失败就停，修完再继续；不要带病跑。

### 15.3 停止条件

- 外壳温度 >60°C；
- 扫齿/卡死/异常声；
- ESP32 复位/IMU 掉线；
- 电源电压跌落 >0.5V；
- 结构裂纹/舵盘松动。

### 15.4 验收

- [ ] 每面 ≥8/10；
- [ ] 100 次无硬件损坏；
- [ ] 电流/温度在安全范围；
- [ ] 失败可复现/可解释；
- [ ] 记录完整。

---

## 16. 故障排查矩阵

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 串口没有 COM 口 | 充电线/驱动/板子 | 换数据线；装 CP210x/CH340；按 BOOT 再上电 |
| 串口有口但无输出 | USB CDC 未开/用了 UART 口 | Arduino IDE 设 USB CDC On Boot=Enabled；或改接 UART 口/加 build flag |
| `IMU not found` | 3.3V/GND/SDA/SCL/地址/启动等待 | 逐项量电压/通断；I²C 扫描 0x23；确认 5s 等待 |
| IMU 灯不亮/扫描无设备 | VCC 误接 5V5/6V，或 GND/接线松 | 断电，VCC 改 3V3；量 3.3V；仍不亮则模块可能损坏 |
| CH3/CH4 做 I²C 找不到 | 信号脚串阻/上拉到 6V/线太长 | 换两个备用口；确认信号对 V+ 高阻；缩短线/加 3.3V 上拉 |
| IMU 版本可读但 `up` 不对 | 安装方向/轴映射 | 按 +X 前/+Y 左/+Z 上装；改 `raw_to_si()` |
| 陀螺读数异常/`up` 乱跳 | 模块批次寄存器不连续，或 0x04–0x0F 不能一次读 | 改成两次 6 字节读取（0x04 加速度、0x0A 陀螺）；先用 `imu_module_i2c_test` 对照 |
| IMU 反应明显滞后 | 模块 ODR 出厂 25 Hz | 用厂商工具/串口协议设为 100 Hz，再做 `c` 校准 |
| 陀螺校准失败 | 手持/晃动/模块异常 | 放稳 2s；检查模块；重启 |
| 舵机不动 | 6V 没上/共地/信号映射/插反 | 量 V+；查信号到 GPIO；`t`；换一个舵机 |
| `ledcAttach failed` / 舵机无 PWM | ESP32-S3 LEDC 最大 14 位，代码用了 16 位 | 本代码已改为 `SERVO_RES_BITS=14`；确认没有旧的 16 位固件/缓存 |
| 上电瞬间手臂猛跳 | 舵盘不在 1520µs 中位 | 用 center sketch 重新装舵盘 |
| 方向反 | 符号/舵盘装反 | 改 `SERVO_*_SIGN` 或重装；不要反接电源 |
| 舵机抖/ESP32 复位 | 电源/电容/线径/共地 | 6V/5A；1000–2200µF；短粗线；共地；分开供电 |
| 手臂卡住 | 机械干涉 | 停；修结构；不要靠策略绕开 |
| `g` 后不动 | 没 `g`/在 hold/`x` 后没 `r` | 先 `r`，再 `g`；看串口状态 |
| 越推越倒 | IMU/关节符号反 | 停；`t` 检查方向；改符号/轴 |
| 站不起来 | 策略/质量/力矩/摩擦 | 称重改 XML；重训；6V/5A；检查末端垫 |
| 训练 OOM | n-envs/batch 太大 | 减 `--n-envs`；关其他程序 |
| `n_steps * n_envs < batch_size` | n-envs 太小 | 用 `--n-envs 2` 或 4 |
| `ModuleNotFoundError` | 没激活 venv/没装依赖 | 激活 `.venv`；`pip install -r ...` |
| `export --verify` 失败 | 没装 clang | 不跑 `--verify`，或安装 LLVM/clang |
| 导出的策略不动 | 维度/路径/没重烧 | 检查 10→128→128→2；覆盖 `policy_b.h` 后重编译 |

---

## 17. 附录 A：引脚与常量

| 功能 | 值 |
|---|---|
| IMU SDA/SCL | GPIO6 / GPIO7（CH3/CH4 信号脚） |
| IMU VCC/GND | 3V3 / CH3-CH4 GND 或 ESP32 GND |
| 肩/肘 PWM | GPIO4 / GPIO5（示例） |
| LED | GPIO2 |
| IMU 地址/时钟 | 0x23 / 100 kHz |
| IMU 启动等待 | 5000 ms |
| 舵机中位 | 1520 µs |
| 舵机行程 | 500–2500 µs |
| `Q_HALF_RANGE` | 1.55 rad |
| `MAX_CMD_RATE` | 0.12 rad/20ms |
| 控制周期 | 20 ms（50 Hz） |
| 舵机电源 | 6V/≥5A |

对应文件：[`../firmware/sr_support_b_ptk/include/config.h`](../firmware/sr_support_b_ptk/include/config.h)

---

## 18. 附录 B：串口命令与输出

| 命令 | 行为 |
|---|---|
| `g` | 运行策略 |
| `s` | 停止策略，保持最后目标 |
| `x` | detach PWM（卸力）；之后 `r` 重新初始化 |
| `r` | 重新初始化 PWM、回中位 |
| `c` | 重新校准陀螺（保持静止） |
| `t` | 关节 ±0.5 rad 自检 |

遥测（250 ms）：

```
up ux uy uz | w wx wy wz | q q1 q2 | qd dq1 dq2 | run/hold
```

启动：

```
waiting for IMU startup 5000 ms...
IMU version x.y.z
Calibrating gyro: keep the robot still
gyro bias (rad/s): ...
servo start q: 0.00 0.00 rad
ready; send g to run
```

---

## 19. 附录 C：文件与命令速查

| 用途 | 路径/命令 |
|---|---|
| 主固件 | `firmware/sr_support_b_ptk/` |
| 固件配置 | `firmware/sr_support_b_ptk/include/config.h` |
| 策略 header | `firmware/sr_support_b_ptk/include/policy_b.h` |
| 中位 sketch | `firmware/servo_center_ptk/servo_center_ptk.ino` |
| 训练 | `training/b_line/` |
| 实机 STL | `D:\Project\3D-Models\self-rising-robot\source\`（无许可证，仅本地使用） |
| 仿真模型 | `training/b_line/assets/robot_selfrising.xml`（由 `tools/build_selfrising_model.py` 生成） |
| B 线备选 CAD | `hardware/juxi_b_line/` |
| 引脚记录 | `docs/pinmap.md` |
| BOM | `bom/bom.md` |
| 烧录 | `pio run -d firmware/sr_support_b_ptk -t upload` |
| 串口 | `pio device monitor --rts 0 --dtr 0 -b 115200 -p COM5` |
| 训练 | `python -m training.b_line.train --robot selfrising --steps 3000000 --n-envs 4 --hidden 128` |
| 评估 | `python -m training.b_line.evaluate --robot selfrising --episodes 100 --dr --per-face` |
| 导出 | `python -m training.b_line.export_policy --robot selfrising` |

---

## 20. 附录 D：许可与来源

- B 线固件/仿真基于 Juxi-Technology/2dof-selfrighting-robot：**MIT OR Apache-2.0**；见 [`../third_party/juxi-2dof/`](../third_party/juxi-2dof/)。
- 实机 STL 来自 SelfRisingRobot：**无许可证**，仅本地仿真实机、不随产品/公开仓库分发；商用需作者许可或自行重画。
- B 线备选 CAD/STL/STEP：**CERN-OHL-S-2.0**；见 [`../hardware/juxi_b_line/`](../hardware/juxi_b_line/)。
- B 线固件不链接 Feetech SCServo（GPL-3.0）；A 线才会。
- 不使用 SelfRisingRobot 的代码/STL/waypoint；基线 `policy_b.h` 只作 bring-up。
- 商用/分发前：CERN 义务、Arduino LGPL、专利 FTO（CN109693729A/B 等）请法务/专利代理人复核。

---

## 21. 附录 E：验收记录模板

```
日期：
操作人：
硬件序列：
  ESP32-S3：
  IMU：
  舵机 1（肩）：
  舵机 2（肘）：
  转接板：
打印质量：
  底座：____ g
  大臂：____ g
  小臂：____ g
  整机：____ g
尺寸：
  肩高：____ mm
  大臂：____ mm
  小臂：____ mm
IMU：
  版本：____
  直立 up：____
  轴向：通过/不通过
舵机：
  中位：____ µs / ____ µs
  t 自检方向：通过/不通过
  s/x/r：通过/不通过
基线策略：通过/不通过（仅方向）
训练：
  命令/seed/步数：
  标称成功率：
  DR 成功率：
  逐面：
实机：
  roll_pos：__/10
  roll_neg：__/10
  pitch_pos：__/10
  pitch_neg：__/10
  100 次可靠性：
问题/备注：
```

---

## 22. 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-20 | 首版客户复现手册；B 线、I²C IMU、PTK7452、6V/5A、训练/评估/导出流程 |
