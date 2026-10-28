# Firmware / 代码项目

本目录只放代码项目；文字说明在 [`../docs`](../docs)，BOM 在 [`../bom`](../bom)，串口/训练工具在 [`../tools`](../tools) 与 [`../training`](../training)。

| 项目 | 用途 | 状态 |
|---|---|---|
| [`sr_support_b_ptk/`](sr_support_b_ptk/) | **当前主项目**：Juxi B 线固件，PTK7452MG 180° PWM + Juxi IMU + 无源直连转接板；10 维观测/128×128 策略 | 基于 Juxi MIT 代码；**已编译/已烧录**，IMU 待接 |
| [`i2c_scanner/`](i2c_scanner/) | B 线 IMU 地址/接线诊断（GPIO6/7，扫 0x23） | 已编译；诊断用 |
| [`servo_center_ptk/`](servo_center_ptk/) | 装配前舵机 1520 µs 中位辅助 sketch（不需要 IMU） | 辅助工具，未实机 |
| [`sr_support_2dof/`](sr_support_2dof/) | 之前的 8 路/PCA9685/waypoint 骨架；保留用于手动整定/8 路测试 | 骨架，未实机 |
| [`imu_module_i2c_test/`](imu_module_i2c_test/) | Juxi 6 轴 IMU I²C 读取测试 | 参考，未实机 |
| [`reference_2servo_esp32/`](reference_2servo_esp32/) | 底部方位 + 顶部打击两舵机骨架 | 参考，未实机 |
| [`reference_sg90_esp32/`](reference_sg90_esp32/) | MPU6050 + 单舵机备用固件 | 参考，未实机 |

配套：

- [`../training/b_line/`](../training/b_line/)：B 线 MuJoCo/PPO 训练、评估、策略导出。
- [`../hardware/juxi_b_line/`](../hardware/juxi_b_line/)：B 线 CAD/STL（CERN-OHL-S）。
- [`../tools/sr_tune.py`](../tools/sr_tune.py)：旧 8 路/手动整定工具；B 线固件用自带 `t` 自检和串口命令。

> 所有固件都未在实机验证；本机没有 Arduino/ESP32 C++ 编译环境。首次烧录先只接 USB、再给舵机上电。  
> 许可：B 线固件基于 Juxi-Technology/2dof-selfrighting-robot（MIT/Apache-2.0）；见 [`../third_party/juxi-2dof/`](../third_party/juxi-2dof/)。
