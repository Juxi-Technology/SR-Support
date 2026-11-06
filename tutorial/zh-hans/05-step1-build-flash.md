---
title: 05 第一步：环境、构建与烧录
description: 使用 PlatformIO 构建并烧录 SR-Support B 线固件，串口命令与启动日志说明。
---

# 05 第一步：环境、构建与烧录

> **成品用户可跳过本页**：出厂已烧录并验证固件。仅在升级固件或自行修改代码后重新执行。

## 5.1 环境

- **PlatformIO（Arduino framework）**，不是 ESP-IDF；
- 平台：`espressif32 8.0.0`，Arduino core 3.3.12；
- 工程：`firmware/sr_support_b_ptk/`（环境名 `ptk7452`）；
- 本仓库自带项目内 PlatformIO：`.venv-pio/Scripts/pio.exe`（Windows）；首次使用先安装：
  `powershell -ExecutionPolicy Bypass -File tools/install_platformio.ps1`
  （需要 Python 3.12 + `py` 启动器）。

**电脑端 Python 工具**（监控、零点、Twin 镜像）依赖 pyserial/numpy/mujoco/gymnasium，二选一：

- 推荐：项目内虚拟环境 `.venv`（与 PlatformIO 的 `.venv-pio` 相互独立）：
  `powershell -ExecutionPolicy Bypass -File tools/install_tools_env.ps1`；
- 不用虚拟环境也可以：在任意 Python 3.10+ 环境执行 `pip install -r tools/requirements.txt`，
  并把后文命令中的 `.venv\Scripts\python.exe` 换成 `python`。

> 虚拟环境不是硬性要求，只是隔离依赖、避免与系统 Python 冲突（MuJoCo 对版本较敏感，
> 建议使用）。PlatformIO 同理：也可以用 VS Code 插件或全局 `pio`，把
> `.venv-pio\Scripts\pio.exe` 换成对应命令即可。

## 5.2 构建与烧录

```bash
# 构建
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk

# 烧录（COM27 换成实际串口）
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> 烧录前必须关闭占用串口的程序（串口监视器、`tools/hw_monitor.py` 等），否则会报
> `could not open port` / `Access is denied`。

构建成功时资源占用约 RAM 56%、Flash 30%（含 WiFi 与网页服务；不含 WiFi 的早期版本约 7%/12%）。

## 5.3 串口监视

```bash
.venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

打开串口会触发 ESP32 复位；复位后应看到：

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 5.4 串口命令（115200）

| 命令 | 作用 |
|---|---|
| `g` | 开始/继续运行（本版本上电默认自动运行，一般不需要） |
| `s` | 停止执行器，PWM 保持最后目标 |
| `x` | 急停：释放 PWM（舵机卸力），之后需 `r` 重新初始化 |
| `r` | 重新初始化 PWM 并回中位 |
| `t` | 舵机自检（小幅动作） |
| `c` | 标定陀螺 + **加速度计零点**（机器人须**站立在水平桌面**、保持静止；零点写入 NVS） |
| `m <q1> <q2>` | 手动设置两关节目标角（rad） |
| `1/2` | 手动肩关节 ±0.5 rad |
| `3/4` | 手动肘关节 ±0.5 rad |
| `0` | 手动回中 |
| `l` | 3 秒 50 Hz 快速日志 |
| `k` | 打印两舵机中位脉宽 |
| `o` / `p` | 肩中位脉宽 ±10 µs 微调 |
| `z` | 编码器式清零：当前姿态设为两关节 q=0 并打印新脉宽（仅内存；见 [02 页](./02-zero-tool)） |
| `d` | 开关 50 Hz Twin 流（供 MuJoCo 镜像；状态页有同等开关） |
| `w` | 开/关 WiFi（热点 + 状态页/配网，见 [08 页](./08-step4-wifi-twin)） |
| `v` / `b` | 翻转肩 / 肘方向符号 |
| `i` / `j` | 翻转 IMU X / Y 符号 |
| `h` | 站立收臂回中开关（旧策略用） |
| `a` | 旧的脚本扶正模式（legacy，仅测试用） |

## 5.5 上电行为

固件启用 `AUTORUN_ON_BOOT`：上电后执行器处于待命状态，等机器人**完全倒下且静止**
0.5 秒后自动开始扶正，无需发送 `g`。上电时请让机器人保持直立。
