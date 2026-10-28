# BOM / 配件选型（B 线）

- [`bom.md`](bom.md)：人读版，B 线（PTK7452MG）物料、电源、接线、方案分支。
- [`bom.csv`](bom.csv)：表格版，可直接用 Excel/表格软件打开。

当前目标：**B 线 2-DOF 自起立**（2× PTK7452MG 180° PWM + ESP32-S3 + Juxi IMU + 无源直连转接板）。

已有：PTK7452MG ×8、ESP32-S3 舵机转接板 ×1、ESP32-S3、Juxi 6 轴 IMU。  
v0 只用 **2 个** PTK7452MG，其余 6 个备用/后续扩展。

关键变化：B 线用 **6V/5A** 舵机电源（不是旧的 5V/3A）；PTK7452 在 6V 约 3.4 kg·cm。  
许可：代码 MIT/Apache；硬件 CAD CERN-OHL-S；详见 [`../docs/licensing.md`](../docs/licensing.md)。
