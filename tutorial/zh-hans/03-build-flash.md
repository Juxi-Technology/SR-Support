---
title: 03 烧录主固件
description: 用预编译 bin（Flash Download Tool / esptool）或 PlatformIO 源码构建烧录 SR-Support B 线固件，串口命令与启动日志说明。
---

# 03 烧录主固件

> **成品用户可跳过本页**：出厂已烧录并验证固件。仅在升级固件或自行修改代码后执行。
> 客户直接烧预编译固件（3.1，不需要 PlatformIO）；开发者从源码构建（3.2）。

## 3.1 烧录预编译固件（推荐给客户）

1. 确认有 `firmware/releases/sr_support_b_ptk_factory.bin`（校验和见同目录
   `SHA256SUMS`）；
2. 进入下载模式：按住 **BOOT**，点按一下 **RST**，松开 **BOOT**；
3. 烧录（工具安装见 [02 页 2.4](./02-environment.md)；以下命令在 `SR-Support` 目录、
   已激活 `.venv` 的终端里执行）：
   - Windows 图形界面：Flash Download Tool → ESP32-S3 → `0x0` 加载 bin → START；
   - Windows / Linux / macOS 命令行：

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. 烧录完成后按 RST 启动，按下节 3.3 查看日志。

> 烧录 / 串口调试时可以用 USB 给 ESP32 供电、5 V 电源只供舵机（见 [04 页 4.4](./04-assembly.md)
> 的两种供电方式）。

> 命令本身 **Windows / Linux / macOS 通用**：`python -m esptool ...` 写法相同，只需把
> `COM27` 换成实际串口（Windows 如 `COM27`，Linux 如 `/dev/ttyACM0`，macOS 如
> `/dev/tty.usbmodem*`）。Flash Download Tool 仅 Windows，其他系统用 esptool 命令行。

> 装配找中不需要第二个固件：烧好本固件后上电，两舵机自动走到固件零点（1681 / 1456 µs），
> 断电即可装舵盘（见 [04 页 4.2](./04-assembly.md)）；也可以发 `e` 让舵机到 1520 µs 电气中位
> 再装（可选，等价做法）。

## 3.2 从源码构建与烧录（开发者）

环境见 [02 页 2.5](./02-environment.md)。工程：`firmware/sr_support_b_ptk/`（环境名 `ptk7452`）。

```bash
# 构建
pio run -d firmware/sr_support_b_ptk

# 烧录（COM27 换成实际串口）
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> 命令在 `SR-Support` 目录下、已激活 `.venv` 的终端里执行（02 页 2.3），三平台通用；
> `--upload-port COM27` 同样换成实际串口。烧录前必须关闭占用串口的程序（串口监视器、
> `tools/hw_monitor.py` 等），否则会报 `could not open port` / `Access is denied`。

构建成功时资源占用约 RAM 56%、Flash 30%（含 WiFi 与网页服务；不含 WiFi 的早期版本
约 7%/12%）。

## 3.3 串口监视

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

（同样三平台通用，`-p COM27` 换成实际串口。）

> **Windows 图形串口助手（可选）**：野人家园 **UartAssist**（免费、单文件、仅 Windows）。
> 官方页面 <https://cmsoft.cn/resource/101.html>，官方下载入口
> <https://cmsoft.cn/resource/download/101>。打开后选 COM 口、**115200、8N1、无流控**，
> 勾选"发送新行"；接收区看启动日志与遥测，发送框输入命令。请从官方链接下载（第三方
> 下载站常捆绑软件），不要把 exe 放进本仓库分发。

**Linux / macOS 串口查看（任选一种）**：

- 首选：上文的 `pio device monitor`（已随项目安装，跨平台）；
- 轻量命令行：`python -m serial.tools.miniterm /dev/ttyACM0 115200`
  （macOS 用 `/dev/tty.usbmodem*`；退出按 `Ctrl-]`）；也可用系统自带的
  `screen /dev/ttyACM0 115200`（退出 `Ctrl-A` 再按 `K`）；
- 图形界面：**CoolTerm**（免费，Windows/macOS/Linux，官网
  <https://freeware.the-meiers.org>）；Linux 也可 `sudo apt install cutecom`。

> Linux 需要把当前用户加入 `dialout` 组：`sudo usermod -aG dialout $USER`，重新登录生效。

打开串口会触发 ESP32 复位；复位后应看到：

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 串口命令（115200）

所有命令都在串口监视器/串口助手的**发送框**输入并回车（UartAssist 勾选"发送新行"）；
`m` 命令要带空格和两个数值，例如 `m 0.5 0`。

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
| `z` | 编码器式清零：当前姿态设为两关节 q=0 并打印新脉宽（仅内存；见 [05 页](./05-zero-tool.md)） |
| `e` | 电气中位（可选）：两舵机输出 1520 µs，供按电气中位装舵盘；常规做法是上电到固件零点后装盘（见 [04 页 4.2](./04-assembly.md)） |
| `d` | 开关 50 Hz Twin 流（供 MuJoCo 镜像；状态页有同等开关） |
| `w` | 开/关 WiFi（热点 + 状态页/配网，见 [08 页](./08-wifi-twin.md)） |
| `v` / `b` | 翻转肩 / 肘方向符号 |
| `i` / `j` | 翻转 IMU X / Y 符号 |
| `h` | 站立收臂回中开关（旧策略用） |
| `a` | 旧的脚本扶正模式（legacy，仅测试用） |

## 3.5 上电行为

固件启用 `AUTORUN_ON_BOOT`：上电后执行器处于待命状态，等机器人**完全倒下且静止**
0.5 秒后自动开始扶正，无需发送 `g`。上电时请让机器人保持直立。

---

[← 返回教程目录](./index.md)
