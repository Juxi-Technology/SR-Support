---
title: 09 MuJoCo 仿真与实机实时镜像
description: 本地 MuJoCo 仿真窗口（四姿态扶正回放）、实机 WiFi 实时镜像与遥测落盘。
---

# 09 MuJoCo 仿真与实机实时镜像

MuJoCo 在本项目里有两种用法，都用 `hardware/v1/robot_v1.xml`（与实机同源的模型）：

- **本地仿真**：不接实机，在电脑上循环回放四种躺姿的扶正过程，验证参考序列、观察动作；
- **实机实时镜像**：实机通过 WiFi 把姿态数据发到电脑，MuJoCo 窗口实时显示实机动作
  （数字孪生）。

两种用法的窗口操作相同：左键拖动旋转视角、右键拖动平移、滚轮缩放。首次使用前按
[02 页](./02-environment.md) 创建并激活 `.venv`，并在其中装好工具依赖
（`pip install -r tools/requirements.txt`，见 02 页）。

## 9.1 本地仿真窗口

在 `SR-Support` 目录下（先激活 `.venv`）：

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

窗口标题为 `MuJoCo : sr_support_v1`（图 9-1）。机器人被依次摆成四种躺姿
（`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`），每次执行与固件完全相同参数的
参考序列直到站起，然后换下一种姿态循环，直到关闭窗口。终端同步打印当前姿态与结果：

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` 表示该姿态在仿真中扶正成功。出现 `ok=False` 时，对照
[06 调试页](./06-debug-and-calibrate.md) 检查参考序列与你改动过的参数。

![图 9-1 MuJoCo 仿真窗口（四姿态扶正回放）](../images/sr-support/mujoco/01-mujoco-window.png)

*图 9-1：四姿态循环中的一帧，执行器正在把一个躺姿扶起。*

> 已知模型差异：仿真 1× 质量模型下 `roll_neg` 会打印 `ok=False`（模型手臂质量/摩擦与
> 实机不同，见 [11 参考页](./11-reference.md) 11.4），不影响实机固件。

## 9.2 实机实时镜像（WiFi）

前提：实机已按 [08 页](./08-wifi.md) 配网连上家里的 WiFi，电脑也连同一个网络；状态页
Home WiFi 卡片会显示实机的地址 `Robot IP`，把它复制到下面的命令里。

1. 打开状态页按 `Twin ON`（等价串口发送 `d`）；
2. 在 `SR-Support` 目录、激活 `.venv` 后运行（地址换成状态页上的 `Robot IP`）：

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

窗口中的模型按实机姿态**实时**显示（50 Hz 四元数流），身体自动贴地；手臂触地时被
"挡住"在接触角（模拟实机堵转），不会穿地。

- 电脑直连实机热点时：地址固定为 `192.168.4.1`，
  `python tools/live_twin.py --tcp 192.168.4.1:3333`；
- 有线替代：`python tools/live_twin.py --port COM27`（工具会自动发送 `d` 打开数据流）；
- 离线回放：`python tools/live_twin.py --replay logs/hw_fast_xxx.txt`；
- 镜像只读：除切换数据流外不会向实机发送任何控制命令。

## 9.3 WiFi 遥测落盘

```bash
python tools/tcp_log.py
```

把遥测流保存为 `logs/wifi_<时间>.txt`，用于离线回放（`--replay`）与失败现场分析。
直连热点时默认连接 `192.168.4.1:3333`；走家庭网络时把状态页上的 `Robot IP` 作为参数：

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 仿真与训练参考

`training/b_line/` 提供与固件逐参数一致的执行器、参考序列与仿真环境，用于回放、验证
和参数调整；模型文件说明见 [11 参考页](./11-reference.md) 11.1。

---

[← 返回教程目录](./index.md)
