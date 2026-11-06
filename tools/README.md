# tools — 电脑端工具索引

> 全部在电脑上运行，不烧进 ESP32；依赖见 `requirements.txt`。工具均为本项目独立编写。

## 1. 日常使用（B 线）

| 工具 | 用途 |
|---|---|
| [`live_twin.py`](live_twin.py) | **MuJoCo 实时镜像**：串口 `--port COM27` 或 WiFi `--tcp <Robot IP>:3333`；`--replay` 离线回放 |
| [`hw_shoulder_range.py`](hw_shoulder_range.py) | **方向键零点校准**（`z` 定零 / `k` 读中位），见教程第 05 页 |
| [`tcp_log.py`](tcp_log.py) | WiFi 遥测流落盘（`logs/wifi_*.txt`） |
| [`hw_watch.py`](hw_watch.py) | **固定行实时窗口**：原地刷新 up/角速度/关节角/最后事件，可直接输入命令；事件写 `logs/hw_watch.log` |
| [`hw_monitor.py`](hw_monitor.py) | 串口监控：事件记录 + 5 秒遥测摘要 + 舵机越界检查（`logs/hw_monitor.log`） |
| [`hw_log.py`](hw_log.py) | `l` 快速日志采集（3 s 50 Hz，含原始 IMU） |
| [`hw_check.py`](hw_check.py) | 快速连通性自检（IMU 状态、串口命令往返） |
| [`hw_right.py`](hw_right.py) | 手动扶正脚本（按实测序列分段发 `m` 命令） |
| [`servo_center.py`](servo_center.py) | 舵机回固件 q=0 中位（发 `r`，当前固化 1681/1456 µs；装配找中用 `firmware/servo_center_ptk`） |

## 2. 仿真与验证

| 工具 | 用途 |
|---|---|
| [`play_getup_executor.py`](play_getup_executor.py) | 仿真回放四姿态扶正（MuJoCo 窗口） |
| [`verify_v1_lying_poses.py`](verify_v1_lying_poses.py) | 躺姿验证 + 扶正回放 + 拼图 |
| [`probe_v1_kick_geometry.py`](probe_v1_kick_geometry.py) | 卡死姿态的手臂触地几何探针（楔形泵设计依据） |
| [`search_b39_getup.py`](search_b39_getup.py) | 参考序列来源（历史：搜索出当前四方向序列） |
| [`search_v1_roll_neg.py`](search_v1_roll_neg.py) | v1 模型 roll_neg 仿真搜索（历史） |

## 3. 安装脚本

- [`install_platformio.ps1`](install_platformio.ps1)：项目内 `.venv` 安装 PlatformIO（与工具共用）；
- [`install_tools_env.ps1`](install_tools_env.ps1)：项目内 `.venv` 安装电脑端工具依赖
  （pyserial/numpy/mujoco/gymnasium）；
- [`env_check.py`](env_check.py)：**环境自检**：实际加载并步进 MuJoCo 模型、列出串口
  （安装后用，`env check: PASS` 即正常；教程 02 页）；
- [`install_xtensa_toolchain.ps1`](install_xtensa_toolchain.ps1)：工具链下载卡住时的修复脚本。

所有 Python 命令都在**已激活 `.venv`** 的终端里执行（创建与激活见教程 02 页）：
先 `pip install -r tools/requirements.txt`，再用 `python tools/xxx.py`。



```bash
pip install -r tools/requirements.txt
```
