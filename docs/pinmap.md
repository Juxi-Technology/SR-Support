# 引脚映射（B 线，待口述/核对）

> 当前主方案：**B 线**（2× PTK7452MG 180° PWM + Juxi IMU + 无源直连转接板）。  
> 固件：[`../firmware/sr_support_b_ptk/`](../firmware/sr_support_b_ptk/)；引脚集中在 `include/config.h`。  
> 转接板确认：**无源直连 + 共用舵机电源 + 级联排针，没有 PCA9685/GPIO 扩展**。

## 1. 当前固件示例映射（v0，只驱动 2 个舵机）

| 功能 | ESP32-S3 GPIO | 转接板通道 | 说明 |
|---|---|---|---|
| Juxi IMU SDA | GPIO6 | CH3 信号脚（**优先直连 GPIO6**） | I²C 0x23，100 kHz；本机经 CH3 不稳 |
| Juxi IMU SCL | GPIO7 | CH4 信号脚（**优先直连 GPIO7**） | I²C 0x23，100 kHz；本机经 CH4 不稳 |
| Juxi IMU GND | — | CH3/CH4 GND 或 ESP32 GND | 共地 |
| Juxi IMU VCC | — | **ESP32 3V3** | **不要接 CH3/CH4 的 V+（6V）** |
| 肩舵机信号 | GPIO4 | CH1 | 50Hz PWM；PTK7452 |
| 肘舵机信号 | GPIO5 | CH2 | 50Hz PWM；PTK7452 |
| 备用 | GPIO15 | CH5 | B 线固件不驱动 |
| 备用 | GPIO16 | CH6 | B 线固件不驱动 |
| 备用 | GPIO17 | CH7 | B 线固件不驱动 |
| 备用 | GPIO18 | CH8 | B 线固件不驱动 |
| LED（可选） | GPIO2 | — | 状态灯 |
| 舵机电源 V+ | — | V+/GND 端子 | **6V/≥5A**（7452 约 3.4 kg·cm） |
| ESP32 供电 | USB-C | — | 单独 5V；不要用舵机 6V 给 ESP32 |

**待口述/核对：**

1. 转接板丝印是否就是 CH1..CH8 = GPIO4,5,6,7,15,16,17,18；若不同，以万用表通断为准。
2. 级联排针的引脚顺序（V+/GND/信号）是否每个口一致；插反会烧舵机/板子。
3. 转接板是否真的完全无源（没有稳压、缓冲、上拉/下拉、LED 电阻等）；如果有有源器件，告诉我型号。
4. 舵机电源端子额定电流/线径；6V/5A 是否够 2 个 PTK7452 同时动作。
5. 8 个舵机的用途：B 线只用 2 个；CH3/CH4 借给 IMU；CH5–CH8 备用。

## 2. 供电

- **2 个 PTK7452MG**：6V/≥5A 独立电源（推荐）；7.4V/5A 可接近 4.5 kg·cm，但发热/电流要实测。
- 舵机电源端并 **1000–2200 µF** 电解 + 100 nF；串 5A 保险丝/自恢复保险丝；加电源开关。
- ESP32 用 USB-C 5V；舵机电源与 ESP32 **共地**；不要把 6V/7.4V 接到 ESP32 5V/3V3。
- 不要用电脑 USB 口或 MB102 面包板电源带两个舵机。
- 上电顺序：先接好共地/信号 → 舵机上电 → ESP32 USB；断电反过来。

## 3. 转接板级联注意

- 级联排针通常是把 V+/GND/信号并联到每个舵机口；确认每口的信号引脚只对应一个 GPIO，不要出现两个口共用同一 GPIO。
- 如果级联板把 8 个信号脚固定映射到 GPIO4–11/12–18，按实际映射改 `config.h`；B 线只用其中两路。
- 舵机线不要和 IMU I²C 线长距离并行；I²C 线尽量短，必要时加 4.7k 上拉（模块通常自带）。
- 第一次上电先不接舵机，用万用表确认 V+ 电压和极性；再接一个舵机测试，最后接两个。

## 4. 固件对应关系

| 配置 | 位置 | 说明 |
|---|---|---|
| `PIN_I2C_SDA/SCL` | `include/config.h` | IMU I²C |
| `PIN_SERVO_SHOULDER/ELBOW` | `include/config.h` | 两路 PWM 信号 |
| `PIN_LED` | `include/config.h` | 状态灯，可改 |
| `SERVO_CENTER_US` | `include/config.h` | PTK 常见 1520 µs |
| `SERVO_US_PER_RAD` | `include/config.h` | 636.62（2000 µs / π） |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | `include/config.h` | 方向反了改 ±1 |
| `Q_HALF_RANGE` | `include/config.h` | 1.55 rad（±89°） |
| `MAX_CMD_RATE` | `include/config.h` | 0.12 rad / 20 ms |

> B 线固件没有 PCA9685 分支；如果转接板实际是 PCA9685，需要另写驱动（旧的 `sr_support_2dof` 里有参考实现，但不能直接用于 B 线策略）。  
> CH3/CH4 借给 I²C 前，先用电阻档确认信号脚对 V+ 为高阻（没有 6V 上拉/串阻）；I²C 线尽量短，模块上拉到 3.3V。
