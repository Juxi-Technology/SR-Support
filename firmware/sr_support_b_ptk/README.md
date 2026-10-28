# sr_support_b_ptk — B 线固件（PTK7452MG，180° PWM）

> **完整步骤请按 [`../../docs/build-guide.md`](../../docs/build-guide.md)**；一页检查清单 [`../../docs/checklist.md`](../../docs/checklist.md)。

> 当前主固件。基于 Juxi-Technology/2dof-selfrighting-robot B 线固件（MIT/Apache-2.0），已改为 **PTK7452MG + 无源直连转接板**。
> 来源/许可：[`../../third_party/juxi-2dof/`](../../third_party/juxi-2dof/) · [`../../docs/licensing.md`](../../docs/licensing.md)  
> 状态：**已编译并烧录**（PlatformIO 6.2.0 + espressif32 8.0.0 + Arduino core 3.3.12；RAM 7.6%，Flash 13.0%；COM27 烧录 Hash verified）；**IMU 0x23 与两路舵机 bring-up 通过（`t` 自检）**；机械臂尚未组装，策略未跑。首次上电先手扶、空载、低电压。

## 1. 硬件假设

- ESP32-S3-DevKitC-1（或兼容板）。
- 转接板：**无源直连**，ESP32 GPIO → 3-pin 舵机排针；舵机 V+/GND 共用电源轨，排针可级联；**没有 PCA9685 / GPIO 扩展**。
- 2× PTK7452MG（180° PWM，无位置反馈；v0 只用 2 个，其余备用）。
- Juxi 6 轴 IMU（I²C 0x23、100 kHz、3.3V）。
- 舵机电源：**6V/≥5A**（PTK7452 在 6V 约 3.4 kg·cm）；想接近 B 线训练的 4.5 kg·cm，可用 7.4V/5A，但注意发热/电流。
- ESP32 用 USB-C 5V；舵机电源与 ESP32 **共地**；舵机电源端 1000–2200 µF。

## 2. 接线（示例，按转接板实际丝印确认）

| 器件 | 引脚 | 说明 |
|---|---|---|
| IMU SDA | GPIO6 | I²C 100 kHz；转接板 CH3 信号脚 |
| IMU SCL | GPIO7 | I²C 100 kHz；转接板 CH4 信号脚 |
| IMU VCC | ESP32 3V3 | **不要接 CH3/CH4 的 V+（6V）** |
| IMU GND | CH3/CH4 GND 或 ESP32 GND | 共地 |
| 肩舵机信号 | GPIO4 | 50Hz PWM |
| 肘舵机信号 | GPIO5 | 50Hz PWM |
| LED（可选） | GPIO2 | 状态灯 |
| 舵机 V+ | 6V/5A 电源 + | **不要接 ESP32 3V3/USB 5V** |
| 舵机 GND | 电源 − / ESP32 GND | 共地 |

> 当前 `config.h` 的 GPIO4/5 是示例；等口述实际映射后改 `PIN_SERVO_SHOULDER/ELBOW`。  
> 转接板是级联方式：确认每个排针的 V+/GND/信号顺序一致，避免插反。

## 3. 编译/烧录

> **工具结论：PlatformIO（Arduino framework），不是 ESP-IDF。** 底层是 `esptool`，PlatformIO 会自动调用；不需要 `idf.py`。  
> 本机已装 Core 6.2.0 到项目内 `.venv-pio`；命令可用 `.venv-pio/Scripts/pio.exe`，或先激活 venv。详见 [`../../docs/platformio-install.md`](../../docs/platformio-install.md)。

PlatformIO（推荐）：

```bash
pio run -d firmware/sr_support_b_ptk -t upload
pio device monitor --rts 0 --dtr 0 -b 115200
```

Arduino IDE：

- 打开 `firmware/sr_support_b_ptk/src/main.cpp` 不是有效的 Arduino sketch；本目录是 PlatformIO 结构。  
- 如果必须用 Arduino IDE，新建 sketch，把 `src/*` 和 `include/*` 放到 sketch 目录，确保 `config.h` 在 include 路径；`config.h` 已定义 `ROBOT_PWM`，不需要额外 build flag。
- LEDC API 已兼容 Arduino-ESP32 2.x/3.x。

## 4. 串口命令（115200）

| 命令 | 作用 |
|---|---|
| `g` | 开始/继续运行策略（上电默认保持） |
| `s` | 停止策略，PWM 保持最后目标（不释放力矩） |
| `x` | 急停：detach PWM（舵机卸力）；之后需 `r` 重新初始化 |
| `r` | 重新初始化 PWM、回中位；再发 `g` |
| `c` | 重新校准陀螺（保持静止）；结束后恢复原状态 |
| `t` | 关节 ±0.5 rad 自检；结束后恢复原状态 |
| `1` / `2` | 手动：肩关节 +0.5 / −0.5 rad（保持，便于看方向） |
| `3` / `4` | 手动：肘关节 +0.5 / −0.5 rad |
| `0` | 手动：两关节回中位（仍为 manual 保持） |
| `m q1 q2` | 手动：任意目标角（rad，换行结束），例如 `m 1.55 -1.55` |
| `a` | **脚本自动扶正**：检测到倒地（`up_z<0.5` 持续 0.5 s）后执行实测序列，站起后回中保持；`s` 停止 |
| `v` / `b` | 运行时翻转肩 / 肘方向符号（校准用，重启恢复默认） |
| `i` / `j` | 运行时翻转 IMU X / Y 轴符号（之后发 `c` 重新校准陀螺） |
| `l` | 输出 3 s、50 Hz 快速日志（`F` 行：up/gyro/q/state/原始 IMU）；配合 `tools/hw_log.py` |

> `1`–`4`/`0`/`m` 进入 manual 模式，50 Hz 按 0.12 rad/步限速；`s`/`r`/`g` 都会退出 manual。
> IMU 固定 100 Hz 读取；主循环不再无节流读 I²C（否则读取失败、姿态冻结，策略会抖）。

每 250 ms 输出：

```
up ux uy uz | w wx wy wz | q q1 q2 | qd dq1 dq2 | run/hold/manual
```

> `s` 只是停止策略，舵机仍可能堵转发热；长时间异常请 `x` 或直接断舵机电源。  
> `x` 后舵机卸力，手臂会因重力落下；确认安全后再用。

## 5. 策略（重要）

- `include/policy_b.h` 现在是 **v7（SR 慢接口）策略**（`training/b_line/models/ppo_selfrising_sr5/final.zip` 导出，5 维观测、目标增量 0.08 rad/step，10→128→128→2，Tanh），按估算质量 97.4 g、硬舵机模型（kp=50/kv=0.5）训练。
- 固件内置**站立收臂**：`up_z>0.95` 连续 0.2 s → 目标角以 0.12 rad/20 ms 归零（手臂竖直）并保持；`up_z<0.95` 暂停收臂，`<0.90` 交回策略重试。
- PTK7452 在 6V 只有 3.4 kg·cm；实机打印件称重后，用 [`../../training/b_line/`](../../training/b_line/) 重训并重新导出覆盖 `policy_b.h`。**当前版本按估算质量训练，实机成功率会低于仿真。**
- 观测/动作必须一致：10 维 `[up(3), gyro(3), q(2), qdot(2)]`；目标角 = action × 1.55 rad；每 20ms 最多变化 0.12 rad。

## 6. 上电顺序（建议）

1. 机器人放桌面，手臂大致竖直，周围 30 cm 无遮挡；手扶底座。
2. 只接 USB，确认 IMU 版本、陀螺校准、`ready; send g to run`。
3. 舵机上电（6V/5A），确认无异常电流/发热。
4. 发 `t` 自检，确认两个关节方向；方向反了改 `SERVO_SHOULDER_SIGN`/`SERVO_ELBOW_SIGN` 或重装舵盘。
5. 手扶机器人摆成倒地姿态，发 `g`；一有异常立即 `x` 或断舵机电源。
6. 成功后再逐步放手；记录成功率、电流、温度。

## 7. 与旧的 `sr_support_2dof` 的关系

- `sr_support_2dof/` 是之前的 8 路/waypoint 骨架，保留用于手动整定/8 路测试；**B 线当前主固件是本目录**。
- B 线只用 2 路 PWM（肩/肘），不需要 PCA9685；转接板的 8 路排针只是备用/级联。
- 如果以后要做 8 舵机机构，再回到 `sr_support_2dof` 的 8 路驱动或多路扩展。

## 8. 许可

- 固件基于 Juxi B 线代码（MIT/Apache-2.0）；保留 `third_party/juxi-2dof/` 的许可/来源。
- 不链接 Feetech SCServo（GPL-3.0）；B 线固件可按 MIT/Apache 使用。
- 硬件若使用 Juxi B 线 CAD/STL，属于 CERN-OHL-S-2.0；商用/分发前确认义务。
- 不使用 SelfRisingRobot 的代码/waypoint；`policy_b.h` 仅作基线，最终策略由本项目重训。
