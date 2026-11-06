---
title: 02 环境准备（烧录工具与固件）
description: 开工前准备：预编译固件与官方烧录工具（Flash Download Tool / esptool）、电脑端工具与 MuJoCo 环境、可选的 PlatformIO，确认串口。
---

# 02 环境准备（烧录工具与固件）

> 本页在开工前完成。只烧预编译固件的话**不需要 PlatformIO、不需要编译**；只有要改代码
> 或自己构建固件时才需要开发者环境（2.4）。

## 2.1 前提

- Windows / Linux / macOS 任一系统（教程给出各系统对应的命令）；
- 一根 USB **数据线**（纯充电线无法识别开发板）；
- ESP32-S3-DevKitC-1（8 MB Flash）。

## 2.2 获取代码与预编译固件

- 克隆仓库（或解压收到的 zip），后续命令都在**仓库根目录**执行：

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  （私有仓库需先获得访问权限。）

- **预编译固件**在 `firmware/releases/`：

  | 文件 | 用途 |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | 主固件（烧到 0x0；装配找中也用它，串口发 `e`） |
  | `SHA256SUMS` | 校验和 |

## 2.3 烧录工具（所有客户，二选一）

预编译固件是一个 bin 直接烧，**不需要 PlatformIO、不需要下载工具链**。

**A. Windows 图形界面：乐鑫 Flash Download Tool**

1. 打开乐鑫官方 "Other Tools" 下载页（选 Flash Download Tools）：
   <https://www.espressif.com/zh-hans/support/download/other-tools>
2. 解压运行；ChipType 选 **ESP32-S3**，在 `0x0` 处加载
   `firmware/releases/sr_support_b_ptk_factory.bin`，选串口，点击 **START**。

> Flash Download Tool 只有 Windows 版；Linux/macOS 用下面的 esptool。

**B. Windows / Linux / macOS：esptool（命令行）**

```bash
pip install esptool
```

国内网络慢可用镜像：

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

烧录（`COM27` 换成实际串口；Linux 如 `/dev/ttyACM0`，macOS 如 `/dev/tty.usbmodem*`）：

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

连接失败时进入下载模式：按住 **BOOT**，点按一下 **RST**，松开 **BOOT**。

## 2.4 PlatformIO（仅开发者：从源码构建）

> 不改代码就不需要本节。**注意**：PlatformIO（包括 VS Code + PlatformIO 插件）首次使用
> 都要下载 espressif32 平台与 Xtensa 工具链（约 1 GB，来自 PlatformIO registry 与
> GitHub），国内网络可能很慢或失败，必要时需要代理/VPN；换插件绕不开这一步。

- Windows：`powershell -ExecutionPolicy Bypass -File tools/install_platformio.ps1`
  （需要 Python 3.10+ 与 `py` 启动器；脚本优先 3.12，找不到时退回 `py -3`）；
- Linux/macOS：`pip install platformio`，后文的 `.venv-pio/Scripts/pio.exe` 换成 `pio`；
- 验证：`pio --version`。

## 2.5 电脑端工具与 MuJoCo 环境（Twin/零点/日志）

只烧固件不需要本节；要用方向键零点工具、MuJoCo 实时镜像（`tools/live_twin.py`）、
仿真回放或日志工具时安装。依赖都装在项目内 `.venv`：pyserial、numpy、MuJoCo（3.1+）、
gymnasium。

**Windows**

```bash
powershell -ExecutionPolicy Bypass -File tools/install_tools_env.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt
```

国内网络慢可在 pip 命令后加清华镜像
`-i https://pypi.tuna.tsinghua.edu.cn/simple`；首次安装下载约几百 MB。

**验证：运行环境自检（实际加载并步进 MuJoCo，而不是只做 import）**

```bash
.venv/Scripts/python.exe tools/env_check.py
```

预期最后一行是 `env check: PASS`，并打印类似：

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Linux/macOS 把 `.venv/Scripts/python.exe` 换成 `.venv/bin/python`；没插开发板时
`[--] no serial port found` 是正常提示，不影响 PASS。

> Linux 打开 MuJoCo 窗口若报 GLFW/OpenGL 错误，安装 `libgl1` 与 `libglew-dev`
> （如 `sudo apt install libgl1 libglew-dev`）；Windows/macOS 的 MuJoCo wheel 自带运行库。
> `training/b_line` 的仿真/回放使用同一套依赖，无需再装。

## 2.6 连接开发板，确认串口

1. USB-C 接电脑；Windows 在设备管理器看 COM 号，Linux 通常 `/dev/ttyACM0`（用户需在
   `dialout` 组），macOS 通常 `/dev/tty.usbmodem*`；
2. 记下串口，后文所有 `COM27` 都换成实际值；
3. 串口监视器或 `hw_monitor.py` 占用串口时无法烧录，烧录前先关闭。

## 2.7 环境验证清单

- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` 存在且校验通过
      （`sha256sum -c firmware/releases/SHA256SUMS`）；
- [ ] `python -m esptool version` 正常，或 Flash Download Tool 能打开；
- [ ] 电脑能看到开发板串口；
- [ ] （仅开发者）`pio --version` 正常；
- [ ] `tools/env_check.py` 输出 `env check: PASS`。

全部通过后再进入下一页。
