# tools — 串口整定与日志工具

> 这些工具只跑在电脑上，不烧进 ESP32；依赖见 `requirements.txt`。  
> 工具均为本项目独立编写，无许可证问题。

## 0. PlatformIO 安装脚本

- [`install_platformio.ps1`](install_platformio.ps1)：在项目内创建 `.venv-pio` 并安装 PlatformIO。
- [`install_xtensa_toolchain.ps1`](install_xtensa_toolchain.ps1)：首次编译卡在 `toolchain-xtensa-esp-elf` 时，手动断点续传/校验/解压/注册。

完整说明见 [`../docs/platformio-install.md`](../docs/platformio-install.md)。

```powershell
powershell -ExecutionPolicy Bypass -File tools\install_platformio.ps1
```

## 1. 安装

```bash
pip install -r tools/requirements.txt
```

## 2. 串口整定（`sr_tune.py`）

先烧 `firmware/sr_support_2dof`，确认固件启动、IMU 正常、CSV 输出（默认开）。然后：

```bash
python tools/sr_tune.py --list
python tools/sr_tune.py --port COM5
```

Windows 一般是 `COMx`，Linux 是 `/dev/ttyUSB0` 或 `/dev/ttyACM0`。如果同时记录日志：

```bash
python tools/sr_tune.py --port COM5 --csv run1.csv
```

### 2.1 手动整定流程

1. 输入 `m` 进入手动模式；输入 `1`–`8` 选择要动的舵机（v0 用 1=肩、2=肘）。
2. 输入 `a` / `d` 让选中舵机 −/+5°；`j` / `l` 直接动舵机 2。
3. 把机器人摆成一种倒姿，慢慢试出一条能撑起来的路径。
4. 每到关键姿态，输入 `:w` 捕获当前 `s1_target/s2_target`（工具从 CSV 读取，自动转弧度）。
5. 输入 `:l` 查看已捕获点；`:c` 清空重来。
6. 输入 `:s front`（或 `back/left/right`）生成 `waypoints_front.txt`，里面是可直接粘贴的 C 片段。
7. 把片段填进 `firmware/sr_support_2dof/getup_sequence.h`，把 `GETUP_SEQ_READY` 改成 1，重新编译。

> 捕获的是**目标角**，不是当前角；因为固件是慢速插值，等舵机到位后再 `:w` 更准。  
> 最后一个 waypoint 建议 `{0,0}`，让起立后臂回中。

### 2.2 本地命令

| 命令 | 作用 |
|---|---|
| `:w [name]` | 捕获当前 s1/s2 目标角 |
| `:l` | 列出已捕获 waypoint |
| `:c` | 清空 |
| `:s front` | 保存 C 片段到 `waypoints_front.txt` |
| `:q` | 退出 |
| `:h` | 帮助 |

其余输入原样发给固件：`g` 起立、`x` 急停、`m` 手动/自动、`1`–`8` 选择舵机、`a/d`、`j/l`、`c` 回中、`p` 状态、`s` 舵机状态、`v` 详细输出、`?` 帮助。

> 默认每 0.5s 打印一行摘要；加 `--raw` 打印全部 CSV。

## 3. 日志绘图（`plot_log.py`）

```bash
python tools/plot_log.py run1.csv
python tools/plot_log.py run1.csv --out run1.png
```

画三条曲线：tilt、舵机 1 目标/当前、舵机 2 目标/当前；状态切换处有竖线。x 轴按固件 `PRINT_PERIOD_MS=100`（约 10Hz CSV）估算，仅用于看趋势；如果改了打印周期，时间轴会跟着偏。

## 4. 安全

- 第一次先空载/不装臂，确认 IMU 和舵机方向，再装机械。
- 手动模式也会走 `SERVO_TARGET_DELTA_RAD` 的慢速限幅；但长时间堵转仍会发热。
- 急停 `x` 会 detach PWM（舵机卸力）；恢复用 `r`（会先回中）。
- 不要把 8 个舵机接到 ESP32 的 USB 5V；用独立 5V/6V 电源并共地。
