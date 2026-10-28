# PlatformIO 安装与烧录（Windows）

> 本机实测：2026-10-20，Windows 11，Python 3.12.9，**PlatformIO Core 6.2.0**。  
> 结论：**主固件用 PlatformIO（Arduino framework），不是 ESP-IDF**；底层烧录器是 `esptool`，PlatformIO 自动调用。  
> 本文对应项目：[`../firmware/sr_support_b_ptk/`](../firmware/sr_support_b_ptk/)；完整复现流程见 [`build-guide.md`](build-guide.md)。

---

## 0. 本机已经完成的安装（2026-10-20）

| 项目 | 结果 |
|---|---|
| Python venv | `D:\Project\SR-Support\.venv-pio` |
| PlatformIO Core | **6.2.0**（`6.2.0`） |
| Python | 3.12.9 |
| 安装位置 | `C:\Users\admin\.platformio`（PlatformIO Core Directory） |
| VS Code | 已安装；扩展 `platformio.platformio-ide` 已存在 |
| ESP-IDF 工具链 | `C:\Espressif\tools\xtensa-esp-elf\esp-14.2.0_20241119\xtensa-esp-elf`（GCC 14.2.0） |
| PlatformIO 平台 | `espressif32@8.0.0`（已在 `platformio.ini` 固定） |
| Arduino core | 3.3.12（`framework-arduinoespressif32@4.30312.261016` + S3 libs 3.3.12） |
| 首次编译 | **SUCCESS**，131.76 s；RAM 7.6%，Flash 13.0%（433,513 / 3,342,336 bytes） |
| 产物 | `firmware/sr_support_b_ptk/.pio/build/ptk7452/firmware.bin`（约 429 KB） |
| 串口 | 当前只看到 `COM175`（WCH USB-BLE-SERIAL），**不是 ESP32-S3**；插板后重新 `pio device list` |

验证命令（Git Bash）：

```bash
.venv-pio/Scripts/pio.exe --version
```

```bash
.venv-pio/Scripts/pio.exe system info
```

```bash
.venv-pio/Scripts/pio.exe device list
```

PowerShell 里等价：

```powershell
.\.venv-pio\Scripts\pio.exe --version
```

---

## 0.1 会不会影响原来的 ESP-IDF？

**不会。** 本机实测与证据：

| 项目 | 结果 |
|---|---|
| ESP-IDF 安装位置 | `C:\Espressif`（tools）+ `D:\esp\v5.4.1`、`D:\esp\v6.0.1`（IDF 源码） |
| PlatformIO 安装位置 | `C:\Users\admin\.platformio` + 项目内 `.venv-pio` |
| 工具链关系 | PlatformIO 用的是**独立复制**的 1.3 GB 工具链（inode 不同，不是 junction） |
| `C:\Espressif` 是否被修改 | 否（只读取了 `xtensa-esp32s3-elf-gcc --version`） |
| `D:\esp` 是否被修改 | 否 |
| `eim_idf.json` | 未修改；v5.4.1 和 v6.0.1 条目都在 |
| ESP-IDF 自检 | PowerShell 激活 v6.0.1 后 `idf.py --version` → **ESP-IDF v6.0.1** |

注意：

- **不要在 Git Bash/MSYS 里跑 `idf.py`**，它会报 `MSys/Mingw is no longer supported`；这是 ESP-IDF 自身限制，用 PowerShell 或 Espressif IDE。
- PlatformIO 多占约 1.3 GB（`C:\Users\admin\.platformio\packages\toolchain-xtensa-esp-elf`）；删掉它只影响 PlatformIO，不影响 IDF。
- 不建议把 PlatformIO 包目录改成指向 `C:\Espressif` 的 junction：那样删除/升级 PlatformIO 时可能动到 IDF 工具链。当前用复制，隔离最安全。

---

## 1. 方式 A：VS Code + PlatformIO IDE（推荐日常使用）

1. 安装 VS Code（本机已有）。
2. 扩展商店搜索 **PlatformIO IDE**，安装 `platformio.platformio-ide`。
   - 本机已安装；命令行确认：
     ```bash
     code --install-extension platformio.platformio-ide --force
     ```
3. VS Code：`File → Open Folder` 打开 `firmware/sr_support_b_ptk`。
4. 左下角环境选择 **ptk7452**。
5. 点 **Upload**（→ 箭头图标）烧录。
6. 点 **Monitor**（插头图标），波特率 **115200**。

> VS Code 的 PlatformIO IDE 会使用它自己的 core/penv；和本项目的 `.venv-pio` 可以共存，互不影响。  
> 命令行和 VS Code 不要同时占用同一个串口。

---

## 2. 方式 B：命令行 PlatformIO Core（本机采用）

### 2.1 创建独立 venv

在仓库根目录 `D:\Project\SR-Support`：

```bash
py -3.12 -m venv .venv-pio
```

```bash
.venv-pio/Scripts/python.exe -m pip install --upgrade pip
```

```bash
.venv-pio/Scripts/python.exe -m pip install platformio
```

### 2.2 验证

```bash
.venv-pio/Scripts/pio.exe --version
```

预期：

```
PlatformIO Core, version 6.2.0
```

```bash
.venv-pio/Scripts/pio.exe system info
```

预期能看到：

```
PlatformIO Core             6.2.0
Python                      3.12.9-final.0
System Type                 windows_amd64
Platform                    Windows-11
PlatformIO Core Directory   C:\Users\admin\.platformio
```

### 2.3 一键脚本（可选）

仓库提供 [`../tools/install_platformio.ps1`](../tools/install_platformio.ps1)：

```powershell
powershell -ExecutionPolicy Bypass -File tools\install_platformio.ps1
```

它会创建 `.venv-pio`、安装/升级 PlatformIO、打印版本。

---

## 3. 第一次编译 / 烧录

### 3.1 只编译（不接板子）

```bash
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk
```

**本机实测结果（2026-10-20）：**

```
PLATFORM: Espressif 32 (8.0.0) > Espressif ESP32-S3-DevKitC-1-N8 (8 MB QD, No PSRAM)
 - framework-arduinoespressif32 @ 4.30312.261016 (3.3.12)
 - framework-arduinoespressif32-esp32s3-libs @ 3.3.12
 - toolchain-xtensa-esp-elf @ 14.2.0+20260121
RAM:   7.6% (used 24848 bytes from 327680 bytes)
Flash: 13.0% (used 433513 bytes from 3342336 bytes)
========================= [SUCCESS] Took 131.76 seconds =========================
```

产物：

```
firmware/sr_support_b_ptk/.pio/build/ptk7452/firmware.bin   (约 429 KB)
firmware/sr_support_b_ptk/.pio/build/ptk7452/firmware.elf
```

- 第一次会下载 `espressif32`、Arduino core、ESP32-S3 libs、esptool 等；本机已装好。
- **Xtensa 编译器没有走 PlatformIO 的 401 MB 下载**：复用了本机 ESP-IDF 14.2.0 工具链（见 5.1）。
- 下载缓存在 `C:\Users\admin\.platformio`。

### 3.2 接板子后烧录

1. 用**支持数据的 USB-C 线**连接 ESP32-S3。
2. 查端口：
   ```bash
   .venv-pio/Scripts/pio.exe device list
   ```
   本机 ESP32-S3 当前是 **COM27**（FTDI USB Serial）。
3. 烧录（把 `COMx` 换成实际端口）：
   ```bash
   .venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload --upload-port COMx
   ```
   本机实测：COM27，**SUCCESS 37.40 s**，Hash verified。
4. 串口监视（DTR/RTS 拉低，避免自动复位刷屏）：
   ```bash
   .venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COMx
   ```

> 当前 `COM175` 是 WCH USB-BLE-SERIAL，不是 ESP32-S3；不要烧错端口。ESP32-S3 常见 VID 303A（Espressif）或 CH340/CP210x。

### 3.3 只烧录不重编译

```bash
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload -t nobuild --upload-port COMx
```

---

## 4. 串口 / 驱动 / 烧录模式

- **数据线**：很多 USB-C 线只充电；换一根确认能传数据的。
- **驱动**：
  - 板载 USB-JTAG/CDC：通常免驱；
  - CH340：装 CH340 驱动；
  - CP210x：装 Silicon Labs CP210x 驱动。
- **端口不出现**：
  - 换 USB 口/线；
  - 按住 **BOOT**，再按一下 **RST/EN**，进入下载模式；
  - 松开 BOOT，再执行上传。
- **串口无输出**：
  - 用板上的 USB 口时，Arduino IDE 设 **USB CDC On Boot = Enabled**；
  - PlatformIO 可加：
    ```ini
    build_flags =
        -DARDUINO_USB_CDC_ON_BOOT=1
        -DARDUINO_USB_MODE=1
    ```
  - 或者改用板上的 UART 口 + USB-UART 驱动。
- **上传时占用串口**：关闭 VS Code Monitor、Arduino Serial Monitor、其他串口工具。

---

## 5. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `pio: command not found` | 没激活 venv/没加 PATH | 用完整路径 `.venv-pio/Scripts/pio.exe`，或激活 `.venv-pio` |
| `pip install` SSL/超时 | 网络/代理 | 换网络；配置代理；重试 |
| 首次编译卡在下载 | 平台/工具链大 | 等；检查网络；重试 |
| `Unknown board ID` | 板子名不对 | 用 `esp32-s3-devkitc-1`，或改 `platformio.ini` |
| `ledcAttach`/`ledcSetup` 报错 | Arduino core 版本差异 | 本代码已兼容 2.x/3.x；把完整报错发我 |
| 上传失败 `Failed to connect` | 没进下载模式/端口错 | 按 BOOT+RST；确认 COMx；换线 |
| 上传成功但无日志 | USB CDC 未开/波特率错 | 115200；开 USB CDC；换 UART 口 |
| VS Code 和 CLI 抢串口 | 同时打开 Monitor | 只留一个 |
| 长路径/杀毒软件 | Windows 路径/扫描 | 项目放短路径；杀毒加白 `.platformio`/`.pio` |
| Python 3.13 不兼容 | 依赖 | 用 3.12（本机已验证） |

---

## 5.1 首次编译卡在 `toolchain-xtensa-esp-elf`

这是目前 Windows 上最容易卡住的一步：PlatformIO 需要下载 **401 MB** 的 Xtensa 工具链，网络慢时可能停在 20% 很久。

| 项目 | 值 |
|---|---|
| 包名 | `toolchain-xtensa-esp-elf` |
| 版本 | `14.2.0+20260121`（由 `espressif32@8.0.0` 请求） |
| Windows 包大小 | **401,082,739 bytes**（约 382 MiB） |
| SHA256 | `41db60c7308fe0bd15f2b843069735586509dba4e206b1b632ddc07ff4059c56` |
| 直链 | `https://dl.registry.platformio.org/download/platformio/tool/toolchain-xtensa-esp-elf/14.2.0+20260121/toolchain-xtensa-esp-elf-windows_amd64-14.2.0+20260121.tar.gz` |

### 方案 0：复用本机 ESP-IDF 工具链（本机采用，推荐）

你的机器已有 ESP-IDF 6.0 的 Xtensa 工具链：

- `C:\Espressif\tools\xtensa-esp-elf\esp-14.2.0_20241119\xtensa-esp-elf`（GCC 14.2.0）
- `C:\Espressif\tools\xtensa-esp-elf\esp-15.2.0_20251204\xtensa-esp-elf`（GCC 15.2.0）

PlatformIO 不会自动发现它；把它注册到 `%USERPROFILE%\.platformio\packages\toolchain-xtensa-esp-elf` 即可。直接运行脚本：

```powershell
powershell -ExecutionPolicy Bypass -File tools\install_xtensa_toolchain.ps1
```

脚本优先复用 14.2.0；只有找不到时才下载官方 401 MB 包。手动等价步骤：

```powershell
$Src = "C:\Espressif\tools\xtensa-esp-elf\esp-14.2.0_20241119\xtensa-esp-elf"
$Pkg = "$env:USERPROFILE\.platformio\packages\toolchain-xtensa-esp-elf"
robocopy $Src $Pkg /E /NFL /NDL /NJH /NJS /NP
```

然后写 `.piopm`/`package.json`（脚本会自动写；关键是把版本标成 PlatformIO 请求的 `14.2.0+20260121`）：

```powershell
'{"type": "tool", "name": "toolchain-xtensa-esp-elf", "version": "14.2.0+20260121", "spec": {"owner": "platformio", "id": 17066, "name": "toolchain-xtensa-esp-elf", "requirements": null, "uri": null}}' | Set-Content -Encoding ascii "$Pkg\.piopm"
```

再跑：

```bash
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk
```

**本机实测**：这样注册后，PlatformIO 没有再下载 401 MB，直接编译 **SUCCESS（131.76 s）**。  
二进制里 `gcc --version` 显示 `esp-14.2.0_20241119`，但 PlatformIO 的 `.piopm` 标成 `14.2.0+20260121`；本项目的 Arduino core 3.3.12 构建已通过。  
如果以后升级 PlatformIO 平台要求不同 GCC，再改用官方包或 `esp-15.2.0_20251204`。

### 方案 A：等待/重试

先等 10–20 分钟；如果进度条长时间不动，停止构建，重跑：

```bash
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk
```

PlatformIO 可能复用部分缓存，但不保证续传。

### 方案 B：手动下载官方包（备选）

也可以直接跑脚本：

```powershell
powershell -ExecutionPolicy Bypass -File tools\install_xtensa_toolchain.ps1
```

脚本会断点续传、校验 SHA256、解压并写 `.piopm`；可重复执行。

手动步骤（PowerShell）：

```powershell
$Cache = "$env:USERPROFILE\.platformio\.cache\downloads\toolchain-xtensa-esp-elf-14.2.0.tar.gz"
curl.exe -L -C - --retry 3 --retry-delay 2 -o $Cache "https://dl.registry.platformio.org/download/platformio/tool/toolchain-xtensa-esp-elf/14.2.0+20260121/toolchain-xtensa-esp-elf-windows_amd64-14.2.0+20260121.tar.gz"
```

校验：

```powershell
Get-FileHash $Cache -Algorithm SHA256
# 必须是 41DB60C7308FE0BD15F2B843069735586509DBA4E206B1B632DDC07FF4059C56
```

解压并注册：

```powershell
$Pkg = "$env:USERPROFILE\.platformio\packages\toolchain-xtensa-esp-elf"
New-Item -ItemType Directory -Force $Pkg | Out-Null
tar -xzf $Cache -C $Pkg
'{"type": "tool", "name": "toolchain-xtensa-esp-elf", "version": "14.2.0+20260121", "spec": {"owner": "platformio", "id": 17066, "name": "toolchain-xtensa-esp-elf", "requirements": null, "uri": null}}' | Set-Content -Encoding ascii "$Pkg\.piopm"
```

确认：

```powershell
Get-Content "$Pkg\.piopm"
Test-Path "$Pkg\bin\xtensa-esp32s3-elf-gcc.exe"
```

再跑：

```bash
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk
```

> 如果 PlatformIO 仍然尝试重新安装，可在 `platformio.ini` 里临时加：
> ```ini
> platform_packages =
>     platformio/toolchain-xtensa-esp-elf@symlink://C:/Users/admin/.platformio/packages/toolchain-xtensa-esp-elf
> ```
> 这是本机路径的兜底方案；正常安装后不需要。

### 方案 C：网络/代理

- 换网络或配置代理后再重试。
- 公司网络如果拦截 `dl.registry.platformio.org`，让 IT 放行该域名。
- 不要在下载中途反复启动多个 `pio run`，会争抢 `.lock`。

---

## 6. 版本记录与卸载

查看版本：

```bash
.venv-pio/Scripts/pio.exe --version
```

升级：

```bash
.venv-pio/Scripts/python.exe -m pip install --upgrade platformio
```

卸载 CLI：

```bash
.venv-pio/Scripts/python.exe -m pip uninstall platformio
```

彻底清理（可选）：删除 `.venv-pio` 和 `C:\Users\admin\.platformio`（后者包含所有平台/工具链缓存）。

---

## 7. 项目命令速查

| 用途 | 命令 |
|---|---|
| 查串口 | `.venv-pio/Scripts/pio.exe device list` |
| 编译 | `.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk` |
| 烧录 | `.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload --upload-port COMx` |
| 串口 | `.venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COMx` |
| 清理构建 | `.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t clean` |
| VS Code | 打开 `firmware/sr_support_b_ptk`，选 `ptk7452`，Upload/Monitor |

---

## 8. 本机实测记录

| 项目 | 结果 |
|---|---|
| venv 创建 | 成功（`.venv-pio`） |
| PlatformIO 安装 | 成功（6.2.0） |
| VS Code 扩展 | 已安装 |
| ESP-IDF 工具链复用 | 成功（`esp-14.2.0_20241119`，GCC 14.2.0） |
| PlatformIO 平台 | `espressif32@8.0.0`（已固定） |
| Arduino core | 3.3.12 |
| 串口枚举 | 当前仅 COM175（非 ESP32） |
| 首次编译 | **SUCCESS，131.76 s** |
| RAM/Flash | 7.6% / 13.0%（433,513 bytes） |
| 产物 | `firmware/sr_support_b_ptk/.pio/build/ptk7452/firmware.bin`（约 429 KB） |
| 烧录 | **SUCCESS**（COM27，37.40 s，438,320 bytes，Hash verified） |
| 启动日志 | `ESP-ROM...` → `waiting for IMU startup 5000 ms...` → `IMU not found`（IMU 尚未接，属预期） |
| 实机 | **未完成**（先接 IMU） |

> 编译命令：`.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk`  
> 增量重编译约 19 s；修改代码后正常。  
> 烧录前把 ESP32-S3 接上，用 `pio device list` 确认新的 COMx，不要烧到 COM175。
