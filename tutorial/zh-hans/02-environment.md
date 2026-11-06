---
title: 02 环境准备（虚拟环境、烧录工具与固件）
description: 开工前准备：创建并激活项目 .venv、获取预编译固件与烧录工具（Flash Download Tool / esptool）、可选的 PlatformIO、电脑端工具与 MuJoCo 环境，确认串口。
---

# 02 环境准备（虚拟环境、烧录工具与固件）

> 本页在开工前完成。**命令默认在仓库根目录执行**——就是从 GitHub 下载的 **`SR-Support`
> 文件夹**（解压 zip 时可能叫 `SR-Support-main`，以包含 `firmware/`、`tools/` 的那一层
> 为准）。**所有 Python 命令都在已激活 `.venv` 的终端里执行**（2.3）。只烧预编译固件
> 不需要 PlatformIO、不需要编译，改代码才需要开发者环境（2.5）。

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

## 2.3 创建并激活虚拟环境（.venv）

所有电脑端 Python 工具（esptool、PlatformIO、MuJoCo 工具）都装进项目内**同一个**
`.venv`，并且 `.venv` 必须创建在从 GitHub 下载的 **`SR-Support` 目录**里（zip 解压得到
的目录可能叫 `SR-Support-main`，同样以包含 `firmware/`、`tools/` 的那一层为准）。

先进入这个目录，下面的命令都在这里执行：

**Windows（PowerShell）**

```powershell
cd D:\Project\SR-Support    # 换成你实际存放 SR-Support 的位置
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- 不确定进对没有：运行 `dir`，应该能看到 `firmware`、`tools`、`tutorial` 等文件夹；
- 没有 Python 3.12 时用 `py -3 -m venv .venv`（3.10+ 均可）；
- 若提示"禁止运行脚本"，先在当前窗口执行
  `Set-ExecutionPolicy -Scope Process Bypass`，再重新激活；
- `.\.venv\Scripts\Activate.ps1` 是 venv 自带的 **PowerShell 激活脚本**：开头的 `.\`
  表示"运行当前目录下的脚本"，PowerShell 里必须写，不能只写 `Activate.ps1`。
  换终端时用对应的激活文件：
  - **cmd.exe**：`.venv\Scripts\activate.bat`
  - **Git Bash**：`source .venv/Scripts/activate`
  - 退出虚拟环境：`deactivate`

**Windows（cmd.exe）**

```bat
cd /d D:\Project\SR-Support    # cmd 跨盘符必须加 /d，只写 cd D:\... 不会离开 C 盘
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> 怎么分辨终端：cmd 的提示符是 `C:\...>`，PowerShell 是 `PS C:\...>`。本教程默认用
> PowerShell；用 cmd 时把激活命令换成 `activate.bat` 即可，其余命令相同。
> 不需要管理员权限，普通终端即可。
>
> **激活文件必须和终端匹配**：cmd 用 `activate.bat`，PowerShell 用 `Activate.ps1`。
> 在 cmd 里运行 `.ps1` 不会激活当前窗口（通常没有反应或另开一个窗口）。
> 另外先确认 `.venv` 已创建（`dir` 能看到 `.venv` 文件夹）；没有就先执行
> `py -3.12 -m venv .venv`。

**Linux / macOS**

```bash
cd ~/SR-Support             # 换成你实际存放 SR-Support 的位置
python3 -m venv .venv
source .venv/bin/activate
```

- 不确定进对没有：运行 `ls`，应该能看到 `firmware`、`tools`、`tutorial` 等文件夹。

激活成功后提示符前会出现 **`(.venv)`**。本页其余命令和教程后续所有命令都要在这个
**已激活的终端**里执行；关掉终端再打开时需要重新激活。忘记激活时 `pip` / `python`
会指向系统环境，安装或运行都会出问题。

验证是否激活成功：

- Windows：`where python` 第一条应指向 `...\SR-Support\.venv\Scripts\python.exe`；
- Linux / macOS：`which python` 应指向 `.../SR-Support/.venv/bin/python`。

> **cmd 里激活后屏幕被清空？** 这是 venv 自带的 `activate.bat` 在临时切换控制台代码页
> （`chcp 65001`）时触发的终端重绘，**不是新开终端**。只要新提示符以 `(.venv)` 开头、
> `where python` 指向 `.venv`，就说明激活成功。介意清屏的话用 PowerShell 的
> `Activate.ps1`（不会切换代码页），或直接调用 `.venv\Scripts\python.exe`（不激活）。

> **目录要求（重要）**：`.venv` 必须位于**`SR-Support` 文件夹（仓库根目录）**，不能建在
> 子目录。上面的创建/激活命令都是**相对路径**，所以必须在这个目录里执行——新开终端
> 也要先进入该目录再激活（PowerShell：`cd D:\Project\SR-Support`；cmd：
> `cd /d D:\Project\SR-Support`，换成你的实际路径）；或者用绝对路径激活，如
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`。
>
> 激活之后可以 `cd` 到任意子目录，`python` / `pip` / `pio` 仍然指向该 `.venv`；但教程里的
> `tools/...`、`firmware/...`、`hardware/v1/...` 都是相对路径，**请在 `SR-Support` 目录下
> 执行**。`.venv` 与创建时的路径绑定：仓库移动或改名后，删除 `.venv` 重新创建即可。

## 2.4 烧录工具（所有客户，二选一）

预编译固件是一个 bin 直接烧，**不需要 PlatformIO、不需要下载工具链**。
先确认终端位于 `SR-Support` 目录、提示符是 `(.venv)`。

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

## 2.5 PlatformIO（仅开发者：从源码构建）

> 不改代码就不需要本节。**注意**：PlatformIO（包括 VS Code + PlatformIO 插件）首次使用
> 都要下载 espressif32 平台与 Xtensa 工具链（约 1 GB，来自 PlatformIO registry 与
> GitHub），国内网络可能很慢或失败，必要时需要代理/VPN；换插件绕不开这一步。

确认终端在 `SR-Support` 目录、处于 `(.venv)`，然后：

```bash
pip install platformio
```

Windows 也可以运行 `tools/install_platformio.ps1`（同样安装进这个 `.venv`）。验证：

```bash
pio --version
```

> 旧版教程把 PlatformIO 装在单独的 `.venv-pio`；现在统一装进 `.venv`。如果升级后 `pio`
> 提示找不到，就在已激活的 `.venv` 里执行 `pip install platformio`（或重新运行
> `tools/install_platformio.ps1`）即可，旧的 `.venv-pio` 可以删除。

## 2.6 电脑端工具与 MuJoCo 环境（Twin/零点/日志）

只烧固件不需要本节；要用方向键零点工具、MuJoCo 实时镜像（`tools/live_twin.py`）、
仿真回放或日志工具时安装。终端保持在 `SR-Support` 目录、`.venv` 已激活，安装依赖
（pyserial、numpy、MuJoCo 3.1+、gymnasium）：

```bash
pip install -r tools/requirements.txt
```

Windows 也可以运行 `tools/install_tools_env.ps1`（创建/复用 `.venv` 并安装同一组依赖）。
国内网络慢可在 pip 命令后加清华镜像
`-i https://pypi.tuna.tsinghua.edu.cn/simple`；首次安装下载约几百 MB。

**验证：运行环境自检（实际加载并步进 MuJoCo，而不是只做 import）**

```bash
python tools/env_check.py
```

预期最后一行是 `env check: PASS`，并打印类似：

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

没插开发板时 `[--] no serial port found` 是正常提示，不影响 PASS。

> Linux 打开 MuJoCo 窗口若报 GLFW/OpenGL 错误，安装 `libgl1` 与 `libglew-dev`
> （如 `sudo apt install libgl1 libglew-dev`）；Windows/macOS 的 MuJoCo wheel 自带运行库。
> `training/b_line` 的仿真/回放使用同一套依赖，无需再装。

## 2.7 连接开发板，确认串口

1. USB-C 接电脑；Windows 在设备管理器看 COM 号，Linux 通常 `/dev/ttyACM0`（用户需在
   `dialout` 组），macOS 通常 `/dev/tty.usbmodem*`；
2. 记下串口，后文所有 `COM27` 都换成实际值；
3. 串口监视器或 `hw_monitor.py` 占用串口时无法烧录，烧录前先关闭。

## 2.8 环境验证清单

- [ ] 终端位于**仓库根目录**且提示符是 `(.venv)`（`pwd` / `Get-Location` 确认）；
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` 存在且校验通过
      （`sha256sum -c firmware/releases/SHA256SUMS`）；
- [ ] `python -m esptool version` 正常，或 Flash Download Tool 能打开；
- [ ] 电脑能看到开发板串口；
- [ ] （仅开发者）`pio --version` 正常；
- [ ] `python tools/env_check.py` 输出 `env check: PASS`。

全部通过后再进入下一页。
