---
title: 02 环境准备（软件与工具）
description: 开工前先把环境装好：获取代码、安装 PlatformIO 与电脑端 Python 工具、确认 USB 串口。
---

# 02 环境准备（软件与工具）

> 本页在**最开始**完成（打印、装配之前）。装好后，后续所有页面直接使用这里的命令，
> 不再重复安装步骤。

## 2.1 前提

- Windows 10/11（教程命令为 PowerShell + Windows 路径；macOS/Linux 请换成对应 shell 与路径）；
- Python 3.10+ 与 `py` 启动器（推荐 3.12；`py -3.12 --version` 或 `py -3 --version` 能打印版本即可）；
- 一根 USB **数据线**（纯充电线无法识别开发板）。

## 2.2 获取项目代码

从 Git 仓库克隆（或解压收到的 zip），后续命令都在**仓库根目录**执行：

```bash
git clone https://github.com/Juxi-Technology/SR-Support.git
cd SR-Support
```

（私有仓库需先获得访问权限；也可以直接解压拿到的 zip。）

目录速览：`firmware/`（要烧进 ESP32 的固件）、`tools/`（电脑端工具）、
`hardware/v1/`（模型与打印件）、`tutorial/`（本教程）。

## 2.3 安装 PlatformIO（构建与烧录用）

```bash
powershell -ExecutionPolicy Bypass -File tools/install_platformio.ps1
```

脚本在仓库内创建 `.venv-pio` 并安装 PlatformIO，不改系统 Python。验证：

```bash
.venv-pio/Scripts/pio.exe --version
```

> 不想用项目内环境也可以：装 VS Code 的 PlatformIO 插件，或全局
> `pip install platformio`；后文的 `.venv-pio\Scripts\pio.exe` 换成对应命令即可。

## 2.4 安装电脑端工具环境（监控/零点/镜像用）

```bash
powershell -ExecutionPolicy Bypass -File tools/install_tools_env.ps1
```

创建 `.venv` 并安装 pyserial/numpy/mujoco/gymnasium（首次下载约几百 MB，需要几分钟）。验证：

```bash
.venv/Scripts/python.exe -c "import serial, numpy, mujoco, gymnasium; print('tools env ok')"
```

> 虚拟环境不是硬性要求：也可以在任意 Python 3.10+ 里
> `pip install -r tools/requirements.txt`，并把后文的
> `.venv\Scripts\python.exe` 换成 `python`。

## 2.5 连接开发板，确认串口

1. ESP32-S3 用 USB-C 接电脑（板载 USB 串口一般免驱；若设备管理器出现未知串口设备，
   按板子实际芯片安装 CP210x 或 CH340 驱动）；
2. 列出串口：

```bash
.venv-pio/Scripts/pio.exe device list
```

输出中应出现类似 `COM27` 的一行。记住它——后续所有 `COM27` 都换成这个实际端口。
串口监视器、`hw_monitor.py` 等会占用串口，烧录前必须先关闭。

## 2.6 环境验证清单

- [ ] `.venv-pio/Scripts/pio.exe --version` 打印 PlatformIO 版本；
- [ ] `.venv/Scripts/python.exe -c "import serial, numpy, mujoco, gymnasium"` 无报错；
- [ ] `pio device list` 能看到开发板串口（如 `COM27`）；
- [ ] 知道仓库根目录位置（所有命令都在这里执行）。

全部通过后再进入下一页。
