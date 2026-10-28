---
title: 03 固件构建与烧录
description: 使用 PlatformIO 构建并烧录 SR-Support B 线固件，串口命令与启动日志说明。
---

# 03 固件构建与烧录

## 3.1 环境

- **PlatformIO（Arduino framework）**，不是 ESP-IDF；
- 平台：`espressif32 8.0.0`，Arduino core 3.3.12；
- 工程：`firmware/sr_support_b_ptk/`（环境名 `ptk7452`）；
- 本仓库自带项目内 PlatformIO：`.venv-pio/Scripts/pio.exe`（Windows）。

## 3.2 构建与烧录

```bash
# 构建
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk

# 烧录（COM27 换成实际串口）
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> 烧录前必须关闭占用串口的程序（串口监视器、`tools/hw_monitor.py` 等），否则会报
> `could not open port` / `Access is denied`。

构建成功时资源占用约 RAM 7.3%、Flash 11.7%。

## 3.3 串口监视

```bash
.venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

打开串口会触发 ESP32 复位；复位后应看到：

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 串口命令（115200）

| 命令 | 作用 |
|---|---|
| `g` | 开始/继续运行（本版本上电默认自动运行，一般不需要） |
| `s` | 停止执行器，PWM 保持最后目标 |
| `x` | 急停：释放 PWM（舵机卸力），之后需 `r` 重新初始化 |
| `r` | 重新初始化 PWM 并回中位 |
| `t` | 舵机自检（小幅动作） |
| `c` | 重新标定陀螺零偏（保持静止） |
| `m <q1> <q2>` | 手动设置两关节目标角（rad） |
| `1/2` | 手动肩关节 ±0.5 rad |
| `3/4` | 手动肘关节 ±0.5 rad |
| `0` | 手动回中 |
| `l` | 3 秒 50 Hz 快速日志 |
| `k` | 打印两舵机中位脉宽 |
| `o` / `p` | 肩中位脉宽 ±10 µs 微调 |
| `v` / `b` | 翻转肩 / 肘方向符号 |
| `i` / `j` | 翻转 IMU X / Y 符号 |
| `h` | 站立收臂回中开关（旧策略用） |
| `a` | 旧的脚本扶正模式（legacy，仅测试用） |

## 3.5 上电行为

固件启用 `AUTORUN_ON_BOOT`：上电后执行器处于待命状态，等机器人**完全倒下且静止**
0.5 秒后自动开始扶正，无需发送 `g`。上电时请让机器人保持直立。
