# B 线一页式检查清单（打印/照着做）

> 完整说明：[build-guide.md](build-guide.md)  
> 每次上电前先读：[安全 5 条](build-guide.md#0-当前流程与接口结论)。

## 0. 开箱/转接板

- [ ] 2× PTK7452MG，25T，1520 µs，尺寸 23.6×26.9×11.7 mm
- [ ] Juxi 6 轴 IMU，I²C 0x23，3.3V
- [ ] ESP32-S3 能被电脑识别
- [ ] 转接板每口 V+ 共通、GND 共通、**信号脚彼此不短路**
- [ ] 每个信号脚对应到具体 GPIO：CH1..CH8 = GPIO4,5,6,7,15,16,17,18
- [ ] CH3/CH4 信号脚作 IMU SDA/SCL；这两个口的 V+ 不接 IMU
- [ ] 板上没有 PCA9685/移位寄存器；没有 V+ 反灌 ESP32
- [ ] **STOP**：信号全并联 / V+/GND 短路 / 电压不对

## 1. 打印/装配

- [ ] b_base、b_arm1、b_arm2 打印完成（PETG）
- [ ] 舵机座不挤压；舵盘孔位对得上
- [ ] 两舵机 1520 µs 中位，舵盘装好时臂竖直向上
- [ ] 手动转两关节全程无卡滞/干涉
- [ ] 末端垫 O 圈装好
- [ ] IMU 印字 +X 前、+Z 上，VHB 固定

## 2. 接线/上电

- [ ] IMU：3V3 / GND（CH3/CH4 GND 或 ESP32 GND） / SDA=GPIO6 / SCL=GPIO7
- [ ] 肩/肘信号：GPIO4/5（按实际映射）
- [ ] 舵机 V+：6V/5A → 5A 保险丝 → 开关 → 转接板
- [ ] 舵机 GND 与 ESP32 共地
- [ ] 1000–2200 µF + 100 nF 就近；极性正确
- [ ] ESP32 只用 USB-C 5V；**6V 没有接到 ESP32**
- [ ] 不接舵机先测 V+ / 3V3；再接一个、再两个

## 3. IMU 验证

- [ ] 启动日志：`IMU version x.y.z`
- [ ] 如果只有 `IMU not found`：先查 3V3/GND/SDA/SCL；再用 `firmware/i2c_scanner` 确认 0x23
- [ ] `Calibrating gyro...` 后保持静止
- [ ] 直立 `up ≈ +0.00 +0.00 +1.00`
- [ ] 前后/左右倾斜符号正确
- [ ] 无 I²C 掉线；必要时把模块 ODR 设为 100 Hz

## 4. 舵机/安全

- [ ] `t` 自检：肩 q>0 → −Y；肘 q>0 → +X
- [ ] 方向不对：改 `SERVO_*_SIGN` 或重装舵盘
- [ ] `s` 保持；`x` 卸力；`r` 回中；`x` 后必须 `r` 再 `g`
- [ ] 无异常电流/复位；温度 <60°C
- [ ] 单次堵转 ≤1 s

## 5. 基线策略（只验证方向）

- [ ] 手扶、周围 30 cm 清空
- [ ] `g` 后手臂方向合理
- [ ] 异常立即 `x`/断电
- [ ] 不要求站起来（基线是 PTK7465）

## 5.5 中位校准与 WiFi（2026-11 新增，详见 build-guide §9.6/§9.7）

- [ ] 换齿/拆装后：`tools/hw_shoulder_range.py` 方向键摆到目测中位 → 按 `z` → 把打印的 µs 写回 `config.h` 并平移 `EXEC_REF*` / `getup_reference_b39.py` 路点 → 复测四方向
- [ ] 躺姿姿态或镜像倾角异常时：机器人**站立在水平桌面** → 串口 `c`（陀螺+加速度计零点，存 NVS；打印 `accel bias ... (saved)` 才算成功）
- [ ] WiFi：连 `SR-Support` / `srsupport` → 打开 `http://192.168.4.1` 状态页 → Home WiFi `Scan`/`Connect` 配网 → 页面显示 `Robot IP`
- [ ] MuJoCo 无线镜像：状态页 `Twin ON` → `.venv/Scripts/python.exe tools/live_twin.py --tcp <Robot IP>:3333`

## 6. 测量/重训

- [ ] 整机/零件称重
- [ ] 肩高/大臂/小臂/垫位置测量
- [ ] 逐件称重，更新 `hardware/v1/meshes/print_mass_model.json` 与 `hardware/v1/robot_v1.xml` 的质量参数并重新验证
- [ ] `--smoke` 通过
- [ ] 128×128 训练完成（或逐面教师+蒸馏）
- [ ] 标称/DR/逐面评估完成
- [ ] 记录命令/seed/步数/XML 版本

## 7. 导出/实机

- [ ] `export_policy.py` 覆盖 `policy_b.h`
- [ ] 重新编译/烧录
- [ ] `g` 新策略能跑
- [ ] roll_pos / roll_neg / pitch_pos / pitch_neg 各 10 次
- [ ] 每面 ≥8/10
- [ ] 100 次可靠性无硬件损坏
- [ ] 温度/电流/齿轮/螺丝检查
- [ ] 填写验收记录

## 8. 商用/分发前

- [ ] CERN-OHL-S 硬件义务确认
- [ ] Arduino LGPL 评估
- [ ] 专利 FTO（CN109693729A/B 等）
- [ ] 不使用 SelfRisingRobot 代码/STL/waypoint
- [ ] 保留 `third_party/juxi-2dof/` 许可/NOTICE
