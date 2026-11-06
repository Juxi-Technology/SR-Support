---
title: 03 燒錄主韌體
description: 用預編譯 bin（Flash Download Tool / esptool）或 PlatformIO 原始碼建置燒錄 SR-Support B 線韌體，串列埠命令與啟動日誌說明。
---

# 03 燒錄主韌體

> **成品使用者可跳過本頁**：出廠已燒錄並驗證韌體。僅在升級韌體或自行修改程式碼後執行。
> 客戶直接燒預編譯韌體（3.1，不需要 PlatformIO）；開發者從原始碼建置（3.2）。

## 3.1 燒錄預編譯韌體（推薦給客戶）

1. 確認有 `firmware/releases/sr_support_b_ptk_factory.bin`（校驗和見同目錄
   `SHA256SUMS`）；
2. 進入下載模式：按住 **BOOT**，點按一下 **RST**，鬆開 **BOOT**；
3. 燒錄（工具安裝見 [02 頁 2.4](./02-environment.md)；以下命令在 `SR-Support` 目錄、
   已啟用 `.venv` 的終端裡執行）：
   - Windows 圖形介面：Flash Download Tool → ESP32-S3 → `0x0` 載入 bin → START；
   - Windows / Linux / macOS 命令列：

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. 燒錄完成後按 RST 啟動，按下節 3.3 檢視日誌。

> 燒錄 / 串列埠除錯時可以用 USB 給 ESP32 供電、5 V 電源只供舵機（見 [04 頁 4.4](./04-assembly.md)
> 的兩種供電方式）。

> 命令本身 **Windows / Linux / macOS 通用**：`python -m esptool ...` 寫法相同，只需把
> `COM27` 換成實際串列埠（Windows 如 `COM27`，Linux 如 `/dev/ttyACM0`，macOS 如
> `/dev/tty.usbmodem*`）。Flash Download Tool 僅 Windows，其他系統用 esptool 命令列。

> 裝配找中不需要第二個韌體：燒好本韌體後上電，兩舵機自動走到韌體零點（1681 / 1456 µs），
> 斷電即可裝舵盤（見 [04 頁 4.2](./04-assembly.md)）；也可以發 `e` 讓舵機到 1520 µs 電氣中位
> 再裝（可選，等價做法）。

## 3.2 從原始碼建置與燒錄（開發者）

環境見 [02 頁 2.5](./02-environment.md)。工程：`firmware/sr_support_b_ptk/`（環境名 `ptk7452`）。

```bash
# 建置
pio run -d firmware/sr_support_b_ptk

# 燒錄（COM27 換成實際串列埠）
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> 命令在 `SR-Support` 目錄下、已啟用 `.venv` 的終端裡執行（02 頁 2.3），三平臺通用；
> `--upload-port COM27` 同樣換成實際串列埠。燒錄前必須關閉佔用串列埠的程式（串列埠監視器、
> `tools/hw_monitor.py` 等），否則會報 `could not open port` / `Access is denied`。

建置成功時資源佔用約 RAM 56%、Flash 30%（含 WiFi 與網頁服務；不含 WiFi 的早期版本
約 7%/12%）。

## 3.3 串列埠監視

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

（同樣三平臺通用，`-p COM27` 換成實際串列埠。）

> **Windows 圖形串列埠助手（可選）**：野人家園 **UartAssist**（免費、單檔案、僅 Windows）。
> 官方頁面 <https://cmsoft.cn/resource/101.html>，官方下載入口
> <https://cmsoft.cn/resource/download/101>。開啟後選 COM 口、**115200、8N1、無流控**，
> 勾選"傳送新行"；接收區看啟動日誌與遙測，傳送框輸入命令。請從官方連結下載（第三方
> 下載站常捆綁軟體），不要把 exe 放進本倉庫分發。

**Linux / macOS 串列埠檢視（任選一種）**：

- 首選：上文的 `pio device monitor`（已隨專案安裝，跨平臺）；
- 輕量命令列：`python -m serial.tools.miniterm /dev/ttyACM0 115200`
  （macOS 用 `/dev/tty.usbmodem*`；退出按 `Ctrl-]`）；也可用系統自帶的
  `screen /dev/ttyACM0 115200`（退出 `Ctrl-A` 再按 `K`）；
- 圖形介面：**CoolTerm**（免費，Windows/macOS/Linux，官網
  <https://freeware.the-meiers.org>）；Linux 也可 `sudo apt install cutecom`。

> Linux 需要把當前使用者加入 `dialout` 組：`sudo usermod -aG dialout $USER`，重新登入生效。

開啟串列埠後，如果板子剛上電或按過 RST，會先看到啟動日誌；沒有啟動日誌時按一下 RST
再看。復位後應看到：

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 串列埠命令（115200）

所有命令都在串列埠監視器/串列埠助手的**傳送框**輸入並按 Enter（UartAssist 勾選"傳送新行"）；
`m` 命令要帶空格和兩個數值，例如 `m 0.5 0`。

| 命令 | 作用 |
|---|---|
| `g` | 開始/繼續執行（本版本上電預設自動執行，一般不需要） |
| `s` | 停止執行器，PWM 保持最後目標 |
| `x` | 急停：釋放 PWM（舵機卸力），之後需 `r` 重新初始化 |
| `r` | 重新初始化 PWM 並回中位 |
| `t` | 舵機自檢（小幅動作） |
| `c` | 標定陀螺 + **加速度計零點**（機器人須**站立在水平桌面**、保持靜止；零點寫入 NVS） |
| `m <q1> <q2>` | 手動設定兩關節目標角（rad） |
| `1/2` | 手動肩關節 ±0.5 rad |
| `3/4` | 手動肘關節 ±0.5 rad |
| `0` | 手動回中 |
| `l` | 3 秒 50 Hz 快速日誌 |
| `k` | 列印兩舵機中位脈寬 |
| `o` / `p` | 肩中位脈寬 ±10 µs 微調 |
| `z` | 編碼器式清零：當前姿態設為兩關節 q=0 並列印新脈寬（僅記憶體；見 [05 頁](./05-zero-tool.md)） |
| `e` | 電氣中位（可選）：兩舵機輸出 1520 µs，供按電氣中位裝舵盤；常規做法是上電到韌體零點後裝盤（見 [04 頁 4.2](./04-assembly.md)） |
| `d` | 開關 50 Hz Twin 流（供 MuJoCo 鏡像；狀態頁有同等開關） |
| `w` | 開/關 WiFi（熱點 + 狀態頁/配網，見 [08 頁](./08-wifi-twin.md)） |
| `v` / `b` | 翻轉肩 / 肘方向符號 |
| `i` / `j` | 翻轉 IMU X / Y 符號 |
| `h` | 站立收臂回中開關（舊策略用） |
| `a` | 舊的指令碼扶正模式（legacy，僅測試用） |

## 3.5 上電行為

韌體啟用 `AUTORUN_ON_BOOT`：上電後執行器處於待命狀態，等機器人**完全倒下且靜止**
0.5 秒後自動開始扶正，無需傳送 `g`。上電時請讓機器人保持直立。

---

[← 返回教程目錄](./index.md)
