---
title: 11 參考：模型、參數與許可
description: 參考模型檔案（MuJoCo XML / STL）、韌體參數列、四姿態參考序列、驗證狀態與許可。
---

# 11 參考：模型、參數與許可

## 11.1 參考模型檔案

模擬採用 MuJoCo MJCF（`.xml` + `.stl` 網格），與實機同源（自研 v1 設計）：

| 檔案 | 說明 |
|---|---|
| `hardware/v1/robot_v1.xml` | 主模型（與實機幾何/質量對應） |
| `hardware/v1/meshes/*.stl` | 6 個 STL 網格，組裝為 4 組列印件（底座底板/外殼、肩座、上臂支架/肘座、小臂杆） |
| `hardware/v1/meshes/print_mass_model.json` | 逐件列印質量表（15% 填充） |

本倉庫未附帶 URDF；如需 ROS 使用，可由上述 CAD/網格匯出。

## 11.2 韌體關鍵參數（`firmware/sr_support_b_ptk/include/config.h`）

| 參數 | 值 | 說明 |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | 50 Hz 控制週期 |
| `MAX_CMD_RATE` | 0.08 rad/拍 | 每拍輸出限速（4 rad/s） |
| `FALL_UP_Z` | 0.30 | 跌倒門 up_z 閾值 |
| `FALL_W_QUIET` | 0.9 rad/s | 跌倒門角速度閾值 |
| `FALL_CONFIRM_TICKS` | 25 | 跌倒門確認拍數（0.5 s） |
| `EXEC_STEPS_PER_WP` | 20 | 每個參考路點拍數 |
| `EXEC_RETRACT_RATE` | 0.033 rad/拍 | 收臂速率 |
| `EXEC_DONE_TICKS` | 50 | 站立判定持續拍數 |
| `EXEC_TIMEOUT_MS` | 14000 | 單次參考超時 |
| `EXEC_COOLDOWN_TICKS` | 75 | 超時/完成後冷卻（1.5 s） |
| `EXEC_SWITCH_TICKS` | 15 | 姿態切換確認拍數 |
| `EXEC_SWITCH_UP` | 0.60 | 切換時允許的最大 up_z |
| `EXEC_SWITCH_W` | 0.8 rad/s | 切換時允許的最大角速度 |
| `EXEC_MIN_SWITCH_AGE` | 25 | 參考啟動後允許切換的最早拍數 |
| `EXEC_MAX_SWITCHES` | 5 | 單次執行最多切換次數 |
| `EXEC_NEUTRAL_MAX` | 120 | 中立回撤最長拍數 |
| `SERVO_SHOULDER_CENTER_US` | 1681 | 肩零點脈寬（2026-11 視覺中位固化；以 [05 頁](./05-zero-tool.md) 定零為準） |
| `SERVO_CENTER_US` | 1456 | 肘零點脈寬（同上） |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | 肩手動命令限位 |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | 手動範圍（執行器機械行程 ±1.55） |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | 舵機方向 |
| `IMU_YAW90` | 1 | IMU 安裝偏轉 90° 的座標換算 |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | 姿態濾波：加速度修正增益 / 信任帶 |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | 熱點（`w` 開關，上電預設開） |

## 11.3 參考序列（肩, 肘，rad；與 `training/b_line/getup_reference_b39.py` 逐值同步）

| 姿態 | 序列 |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → 收臂` |
| `roll_neg` | `[-1.80,0.70]` 全速直接按壓（保持 ≤40 拍）→ 楔形泵 `[-1.80,0.35] → [-1.80,0.05]` ×2（各保持 ≤30 拍）→ 兜底：`[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]`（鞭甩下砸，保持 ≤40 拍）→ 收尾保持 ≤90 拍 → 收臂 |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → 收臂` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → 收臂` |

## 11.4 驗證狀態與出廠檢驗（2026-11-06）

- **出廠檢驗**：每臺成品在出廠前完成——舵機零點按 [05 頁](./05-zero-tool.md) 逐臺定零並固化、
  IMU 陀螺與加速度計零點標定（NVS）、四方向扶正逐臺測試通過；
- 四個方向實機扶正全部通過，均為**直接起身**（無需翻滾），約 1–6 秒，全程無舵機越界；
- `roll_neg` 最終方案：全行程直接按壓 + 肘部楔形泵 ×2，失敗時鞭甩下砸重試（早期依賴
  "滾過頂部 + 姿態重規劃"的方案已廢棄）；
- 狀態機另經 IMU 加速度計零點標定修正（見 [06 除錯頁 6.2](./06-debug-and-calibrate.md)），
  躺姿姿態與實際一致；
- 模擬 1× 質量模型下 `roll_neg` 不復現（模型手臂質量/摩擦與實機不同），屬已知模型差異，
  實機韌體以實機驗證為準。

## 11.5 許可與來源

- B 線韌體/訓練程式碼：MIT / Apache-2.0；
- B 線 CAD/STL：CERN-OHL-S-2.0（強互惠，商用前確認義務）；
- SelfRisingRobot：無許可證，本教程不包含其程式碼、waypoint 或模型檔案；
- 專利 CN109693729A/B：商用前需完成 FTO 評估。

---

[← 返回教程目錄](./index.md)
