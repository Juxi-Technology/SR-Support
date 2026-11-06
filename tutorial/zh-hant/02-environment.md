---
title: 02 環境準備（虛擬環境、燒錄工具與韌體）
description: 開工前準備：建立並啟用專案 .venv、獲取預編譯韌體與燒錄工具（Flash Download Tool / esptool）、可選的 PlatformIO、電腦端工具與 MuJoCo 環境，確認串列埠。
---

# 02 環境準備（虛擬環境、燒錄工具與韌體）

> 本頁在開工前完成。**命令預設在倉庫根目錄執行**——就是從 GitHub 下載的 **`SR-Support`
> 資料夾**（解壓 zip 時可能叫 `SR-Support-main`，以包含 `firmware/`、`tools/` 的那一層
> 為準）。**所有 Python 命令都在已啟用 `.venv` 的終端裡執行**（2.3）。只燒預編譯韌體
> 不需要 PlatformIO、不需要編譯，改程式碼才需要開發者環境（2.5）。

## 2.1 前提

- Windows / Linux / macOS 任一系統（教程給出各系統對應的命令）；
- 一根 USB **資料線**（純充電線無法識別開發板）；
- ESP32-S3-DevKitC-1（8 MB Flash）。

## 2.2 獲取程式碼與預編譯韌體

- 克隆倉庫（或解壓收到的 zip），後續命令都在**倉庫根目錄**執行：

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  （私有倉庫需先獲得訪問許可權。）

- **預編譯韌體**在 `firmware/releases/`：

  | 檔案 | 用途 |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | 主韌體（燒到 0x0；裝配找中也用它：上電到韌體零點，`e` 可選） |
  | `SHA256SUMS` | 校驗和 |

## 2.3 建立並啟用虛擬環境（.venv）

所有電腦端 Python 工具（esptool、PlatformIO、MuJoCo 工具）都裝進專案內**同一個**
`.venv`，並且 `.venv` 必須建立在從 GitHub 下載的 **`SR-Support` 目錄**裡（zip 解壓得到
的目錄可能叫 `SR-Support-main`，同樣以包含 `firmware/`、`tools/` 的那一層為準）。

先進入這個目錄，下面的命令都在這裡執行：

**Windows（PowerShell）**

```powershell
cd D:\Project\SR-Support    # 換成你實際存放 SR-Support 的位置
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- 不確定進對沒有：執行 `dir`，應該能看到 `firmware`、`tools`、`tutorial` 等資料夾；
- 沒有 Python 3.12 時用 `py -3 -m venv .venv`（3.10+ 均可）；
- 若提示"禁止執行指令碼"，先在當前視窗執行
  `Set-ExecutionPolicy -Scope Process Bypass`，再重新啟用；
- `.\.venv\Scripts\Activate.ps1` 是 venv 自帶的 **PowerShell 啟用指令碼**：開頭的 `.\`
  表示"執行當前目錄下的指令碼"，PowerShell 裡必須寫，不能只寫 `Activate.ps1`。
  換終端時用對應的啟用檔案：
  - **cmd.exe**：`.venv\Scripts\activate.bat`
  - **Git Bash**：`source .venv/Scripts/activate`
  - 退出虛擬環境：`deactivate`

**Windows（cmd.exe）**

```bat
cd /d D:\Project\SR-Support    # cmd 跨磁碟機代號必須加 /d，只寫 cd D:\... 不會離開 C 盤
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> 怎麼分辨終端：cmd 的提示符是 `C:\...>`，PowerShell 是 `PS C:\...>`。本教程預設用
> PowerShell；用 cmd 時把啟用命令換成 `activate.bat` 即可，其餘命令相同。
> 不需要管理員許可權，普通終端即可。
>
> **啟用檔案必須和終端匹配**：cmd 用 `activate.bat`，PowerShell 用 `Activate.ps1`。
> 在 cmd 裡執行 `.ps1` 不會啟用當前視窗（通常沒有反應或另開一個視窗）。
> 另外先確認 `.venv` 已建立（`dir` 能看到 `.venv` 資料夾）；沒有就先執行
> `py -3.12 -m venv .venv`。

**Linux / macOS**

```bash
cd ~/SR-Support             # 換成你實際存放 SR-Support 的位置
python3 -m venv .venv
source .venv/bin/activate
```

- 不確定進對沒有：執行 `ls`，應該能看到 `firmware`、`tools`、`tutorial` 等資料夾。

啟用成功後提示符前會出現 **`(.venv)`**。本頁其餘命令和教程後續所有命令都要在這個
**已啟用的終端**裡執行；關掉終端再開啟時需要重新啟用。忘記啟用時 `pip` / `python`
會指向系統環境，安裝或執行都會出問題。

驗證是否啟用成功：

- Windows：`where python` 第一條應指向 `...\SR-Support\.venv\Scripts\python.exe`；
- Linux / macOS：`which python` 應指向 `.../SR-Support/.venv/bin/python`。

> **cmd 裡啟用後螢幕被清空？** 這是 venv 自帶的 `activate.bat` 在臨時切換控制檯內碼表
> （`chcp 65001`）時觸發的終端重繪，**不是新開終端**。只要新提示符以 `(.venv)` 開頭、
> `where python` 指向 `.venv`，就說明啟用成功。介意清屏的話用 PowerShell 的
> `Activate.ps1`（不會切換內碼表），或直接呼叫 `.venv\Scripts\python.exe`（不啟用）。

> **目錄要求（重要）**：`.venv` 必須位於**`SR-Support` 資料夾（倉庫根目錄）**，不能建在
> 子目錄。上面的建立/啟用命令都是**相對路徑**，所以必須在這個目錄裡執行——新開終端
> 也要先進入該目錄再啟用（PowerShell：`cd D:\Project\SR-Support`；cmd：
> `cd /d D:\Project\SR-Support`，換成你的實際路徑）；或者用絕對路徑啟用，如
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`。
>
> 啟用之後可以 `cd` 到任意子目錄，`python` / `pip` / `pio` 仍然指向該 `.venv`；但教程裡的
> `tools/...`、`firmware/...`、`hardware/v1/...` 都是相對路徑，**請在 `SR-Support` 目錄下
> 執行**。`.venv` 與建立時的路徑繫結：倉庫移動或改名後，刪除 `.venv` 重新建立即可。

## 2.4 燒錄工具（所有客戶，二選一）

預編譯韌體是一個 bin 直接燒，**不需要 PlatformIO、不需要下載工具鏈**。
先確認終端位於 `SR-Support` 目錄、提示符是 `(.venv)`。

**A. Windows 圖形介面：樂鑫 Flash Download Tool**

1. 開啟樂鑫官方 "Other Tools" 下載頁（選 Flash Download Tools）：
   <https://www.espressif.com/zh-hans/support/download/other-tools>
2. 解壓執行；ChipType 選 **ESP32-S3**，在 `0x0` 處載入
   `firmware/releases/sr_support_b_ptk_factory.bin`，選串列埠，點選 **START**。

> Flash Download Tool 只有 Windows 版；Linux/macOS 用下面的 esptool。

**B. Windows / Linux / macOS：esptool（命令列）**

```bash
pip install esptool
```

國內網路慢可用鏡像：

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

燒錄（`COM27` 換成實際串列埠；Linux 如 `/dev/ttyACM0`，macOS 如 `/dev/tty.usbmodem*`）：

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

連線失敗時進入下載模式：按住 **BOOT**，點按一下 **RST**，鬆開 **BOOT**。

## 2.5 PlatformIO（僅開發者：從原始碼建置）

> 不改程式碼就不需要本節。**注意**：PlatformIO（包括 VS Code + PlatformIO 外掛）首次使用
> 都要下載 espressif32 平臺與 Xtensa 工具鏈（約 1 GB，來自 PlatformIO registry 與
> GitHub），國內網路可能很慢或失敗，必要時需要代理/VPN；換外掛繞不開這一步。

確認終端在 `SR-Support` 目錄、處於 `(.venv)`，然後：

```bash
pip install platformio
```

Windows 也可以執行 `tools/install_platformio.ps1`（同樣安裝進這個 `.venv`）。驗證：

```bash
pio --version
```

> 舊版教程把 PlatformIO 裝在單獨的 `.venv-pio`；現在統一裝進 `.venv`。如果升級後 `pio`
> 提示找不到，就在已啟用的 `.venv` 裡執行 `pip install platformio`（或重新執行
> `tools/install_platformio.ps1`）即可，舊的 `.venv-pio` 可以刪除。

## 2.6 電腦端工具與 MuJoCo 環境（Twin/零點/日誌）

只燒韌體不需要本節；要用方向鍵零點工具、MuJoCo 即時鏡像（`tools/live_twin.py`）、
模擬回放或日誌工具時安裝。終端保持在 `SR-Support` 目錄、`.venv` 已啟用，安裝依賴
（pyserial、numpy、MuJoCo 3.1+、gymnasium）：

```bash
pip install -r tools/requirements.txt
```

Windows 也可以執行 `tools/install_tools_env.ps1`（建立/複用 `.venv` 並安裝同一組依賴）。
國內網路慢可在 pip 命令後加清華鏡像
`-i https://pypi.tuna.tsinghua.edu.cn/simple`；首次安裝下載約幾百 MB。

**驗證：執行環境自檢（實際載入並步進 MuJoCo，而不是隻做 import）**

```bash
python tools/env_check.py
```

預期最後一行是 `env check: PASS`，並列印類似：

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

沒插開發板時 `[--] no serial port found` 是正常提示，不影響 PASS。

> Linux 開啟 MuJoCo 視窗若報 GLFW/OpenGL 錯誤，安裝 `libgl1` 與 `libglew-dev`
> （如 `sudo apt install libgl1 libglew-dev`）；Windows/macOS 的 MuJoCo wheel 自帶執行庫。
> `training/b_line` 的模擬/回放使用同一套依賴，無需再裝。

## 2.7 連線開發板，確認串列埠

1. USB-C 接電腦；Windows 在裝置管理器看 COM 號，Linux 通常 `/dev/ttyACM0`（使用者需在
   `dialout` 組），macOS 通常 `/dev/tty.usbmodem*`；
2. 記下串列埠，後文所有 `COM27` 都換成實際值；
3. 串列埠監視器或 `hw_monitor.py` 佔用串列埠時無法燒錄，燒錄前先關閉。

## 2.8 環境驗證清單

- [ ] 終端位於**倉庫根目錄**且提示符是 `(.venv)`（`pwd` / `Get-Location` 確認）；
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` 存在且校驗通過
      （`sha256sum -c firmware/releases/SHA256SUMS`）；
- [ ] `python -m esptool version` 正常，或 Flash Download Tool 能開啟；
- [ ] 電腦能看到開發板串列埠；
- [ ] （僅開發者）`pio --version` 正常；
- [ ] `python tools/env_check.py` 輸出 `env check: PASS`。

全部通過後再進入下一頁。

---

[← 返回教程目錄](./index.md)
