---
title: 09 MuJoCo 模擬與實機即時鏡像
description: 本地 MuJoCo 模擬視窗（四姿態扶正回放）、實機 WiFi 即時鏡像與遙測落盤。
---

# 09 MuJoCo 模擬與實機即時鏡像

MuJoCo 在本專案裡有兩種用法，都用 `hardware/v1/robot_v1.xml`（與實機同源的模型）：

- **本地模擬**：不接實機，在電腦上迴圈回放四種躺姿的扶正過程，驗證參考序列、觀察動作；
- **實機即時鏡像**：實機透過 WiFi 把姿態資料發到電腦，MuJoCo 視窗即時顯示實機動作
  （數字孿生）。

兩種用法的視窗操作相同：左鍵拖動旋轉視角、右鍵拖動平移、滾輪縮放。首次使用前按
[02 頁](./02-environment.md) 建立並啟用 `.venv`，並在其中裝好工具依賴
（`pip install -r tools/requirements.txt`，見 02 頁）。

## 9.1 本地模擬視窗

在 `SR-Support` 目錄下（先啟用 `.venv`）：

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

視窗標題為 `MuJoCo : sr_support_v1`（圖 9-1）。機器人被依次擺成四種躺姿
（`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`），每次執行與韌體完全相同參數的
參考序列直到站起，然後換下一種姿態迴圈，直到關閉視窗。終端同步列印當前姿態與結果：

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` 表示該姿態在模擬中扶正成功。出現 `ok=False` 時，對照
[06 除錯頁](./06-debug-and-calibrate.md) 檢查參考序列與你改動過的參數。

![圖 9-1 MuJoCo 模擬視窗（四姿態扶正回放）](../images/sr-support/mujoco/01-mujoco-window.png)

*圖 9-1：四姿態迴圈中的一幀，執行器正在把一個躺姿扶起。*

> 已知模型差異：模擬 1× 質量模型下 `roll_neg` 會列印 `ok=False`（模型手臂質量/摩擦與
> 實機不同，見 [11 參考頁](./11-reference.md) 11.4），不影響實機韌體。

## 9.2 實機即時鏡像（WiFi）

前提：實機已按 [08 頁](./08-wifi.md) 配網連上家裡的 WiFi，電腦也連同一個網路；狀態頁
Home WiFi 卡片會顯示實機的地址 `Robot IP`，把它複製到下面的命令裡。

1. 開啟狀態頁按 `Twin ON`（等價串列埠傳送 `d`）；
2. 在 `SR-Support` 目錄、啟用 `.venv` 後執行（地址換成狀態頁上的 `Robot IP`）：

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

視窗中的模型按實機姿態**即時**顯示（50 Hz 四元數流），身體自動貼地；手臂觸地時被
"擋住"在接觸角（模擬實機堵轉），不會穿地。

- 電腦直連實機熱點時：地址固定為 `192.168.4.1`，
  `python tools/live_twin.py --tcp 192.168.4.1:3333`；
- 有線替代：`python tools/live_twin.py --port COM27`（工具會自動傳送 `d` 開啟資料流）；
- 離線回放：`python tools/live_twin.py --replay logs/hw_fast_xxx.txt`；
- 鏡像只讀：除切換資料流外不會向實機傳送任何控制命令。

## 9.3 WiFi 遙測落盤

```bash
python tools/tcp_log.py
```

把遙測流儲存為 `logs/wifi_<時間>.txt`，用於離線回放（`--replay`）與失敗現場分析。
直連熱點時預設連線 `192.168.4.1:3333`；走家庭網路時把狀態頁上的 `Robot IP` 作為參數：

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 模擬與訓練參考

`training/b_line/` 提供與韌體逐參數一致的執行器、參考序列與模擬環境，用於回放、驗證
和參數調整；模型檔案說明見 [11 參考頁](./11-reference.md) 11.1。

---

[← 返回教程目錄](./index.md)
