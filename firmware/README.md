# Firmware / 固件项目

本目录只放固件工程；教程在 [`../tutorial`](../tutorial)，手册在 [`../docs`](../docs)，
工具在 [`../tools`](../tools)，训练在 [`../training`](../training)。

| 项目 | 用途 | 状态 |
|---|---|---|
| [`sr_support_b_ptk/`](sr_support_b_ptk/) | **当前主固件**：ESP32-S3 + PTK7452MG（180° PWM）+ Juxi IMU + 无源直连转接板；参考序列执行器、四方向自扶正、WiFi 状态页/配网/MuJoCo 镜像、方向键零点校准 | **已实机验证（四方向通过）** |
| [`i2c_scanner/`](i2c_scanner/) | IMU 地址/接线诊断（GPIO6/7，扫 0x23） | 诊断工具 |
| [`servo_center_ptk/`](servo_center_ptk/) | 装配前舵机中位辅助（PlatformIO 工程，不需要 IMU） | 辅助工具 |
| [`servo_test_ptk/`](servo_test_ptk/) | PTK 舵机单路测试 | 辅助工具 |
| [`imu_module_i2c_test/`](imu_module_i2c_test/) | Juxi IMU I²C 读取测试 | 参考 |

> 旧 `sr_support_2dof`（8 路骨架）与 `reference_*` 示例已随 2026-11 瘦身移除。
> 许可：B 线固件基于 Juxi-Technology/2dof-selfrighting-robot（MIT/Apache-2.0），
> 见 [`../third_party/juxi-2dof/`](../third_party/juxi-2dof/)。
