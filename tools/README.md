# tools — 电脑端工具索引

> 全部在电脑上运行，不烧进 ESP32；依赖见 `requirements.txt`。工具均为本项目独立编写。

## 1. 日常使用（B 线）

| 工具 | 用途 |
|---|---|
| [`live_twin.py`](live_twin.py) | **MuJoCo 实时镜像**：串口 `--port COM27` 或 WiFi `--tcp <Robot IP>:3333`；`--replay` 离线回放 |
| [`hw_shoulder_range.py`](hw_shoulder_range.py) | **方向键零点校准**（`z` 定零 / `k` 读中位），见教程第 02 页 |
| [`tcp_log.py`](tcp_log.py) | WiFi 遥测流落盘（`logs/wifi_*.txt`） |
| [`hw_monitor.py`](hw_monitor.py) | 串口监控：事件记录 + 5 秒遥测摘要 + 舵机越界检查（`logs/hw_monitor.log`） |
| [`hw_log.py`](hw_log.py) | `l` 快速日志采集（3 s 50 Hz，含原始 IMU） |
| [`hw_check.py`](hw_check.py) | 快速连通性自检（IMU 状态、串口命令往返） |
| [`hw_right.py`](hw_right.py) | 手动扶正脚本（按实测序列分段发 `m` 命令） |
| [`servo_center.py`](servo_center.py) | 舵机回中辅助（单发 1520/自定义脉宽） |

## 2. 仿真与验证

| 工具 | 用途 |
|---|---|
| [`play_getup_executor.py`](play_getup_executor.py) | 仿真回放四姿态扶正（MuJoCo 窗口） |
| [`verify_v1_lying_poses.py`](verify_v1_lying_poses.py) | 躺姿验证 + 扶正回放 + 拼图 |
| [`probe_v1_kick_geometry.py`](probe_v1_kick_geometry.py) | 卡死姿态的手臂触地几何探针（楔形泵设计依据） |
| [`search_b39_getup.py`](search_b39_getup.py) | 参考序列来源（历史：搜索出当前四方向序列） |
| [`search_v1_roll_neg.py`](search_v1_roll_neg.py) | v1 模型 roll_neg 仿真搜索（历史） |

## 3. 安装脚本

- [`install_platformio.ps1`](install_platformio.ps1)：项目内 `.venv-pio` 安装 PlatformIO；
- [`install_xtensa_toolchain.ps1`](install_xtensa_toolchain.ps1)：工具链下载卡住时的修复脚本。



```bash
pip install -r tools/requirements.txt
```
