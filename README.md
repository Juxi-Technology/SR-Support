# SR-Support

低成本主动自扶正 / 不倒翁装置。**当前选型：B 线** —— ESP32-S3 + Juxi 6 轴 IMU + 无源直连舵机转接板 + **2× PTK7452MG（180° PWM）**，插电测试，做 2-DOF 自起立。

> 当前状态：B 线固件/训练/CAD 已按 Juxi-Technology/2dof-selfrighting-robot 的 **MIT/Apache** 代码和 **CERN-OHL-S** 硬件整合；已改为 PTK7452MG 参数。**MuJoCo 模型已按你的实机 SelfRisingRobot 3D 打印件重建**（约 97 g），执行器改为 **kp=50/kv=0.5** 以匹配 PTK7452 的硬位置舵机。**v5 策略已导出并烧录进固件**（10→128→128→2，含站立收臂状态机；仿真标称/DR 90%），当前在 `run` 状态等推倒测试；固件另有 `a` 脚本扶正兜底。实机质量仍是估算值，最终需称重重训。固件用 **PlatformIO 6.2.0 + espressif32 8.0.0** 编译烧录（COM27）；IMU 0x23（100 Hz 读取）、两路舵机、手动单关节/任意角命令均已验证；机械已组装。  
> 必读：[docs/build-guide.md](docs/build-guide.md)（**客户版完整复现手册**） · [docs/platformio-install.md](docs/platformio-install.md)（PlatformIO 安装/烧录） · [docs/checklist.md](docs/checklist.md)（一页式检查清单） · [docs/b-line.md](docs/b-line.md)（B 线决定） · [docs/requirements.md](docs/requirements.md)（需求） · [docs/pinmap.md](docs/pinmap.md)（引脚） · [bom/bom.md](bom/bom.md)（BOM） · [docs/licensing.md](docs/licensing.md)（许可）

## 当前方案与备选

| 方案 | 执行器 | 说明 |
|---|---|---|
| **当前主方案：B 线 2-DOF 自起立** | **2× PTK7452MG**（你共有 8 个，v0 用 2 个） | Juxi B 线：2R 臂 + 10 维观测 + 128×128 PPO；180° PWM，无位置反馈 |
| 备选：A 线 | 2× SCS0009 / SCS2332（300° 总线，带反馈） | 仿真更强（99% DR），但要另买舵机+总线板；A 线固件链接 GPL-3.0 SCServo |
| 备选：预防式“倒下前打一下” | HD-1910-C001 总线舵机（9–15 kg·cm） | PTK7452 扭矩/速度不够；见 [docs/b-line.md](docs/b-line.md) 备选方案 |

**不要混用**：PTK7452 适合慢速/中速起立，不适合高速“打一下”；A/B 线机构、固件、CAD 不同。

**许可**：B 线代码 MIT/Apache-2.0；B 线 CAD/STL CERN-OHL-S-2.0；B 线固件不链接 GPL SCServo。SelfRisingRobot 无许可证，本项目的 B 线训练**不使用**它的 waypoint/代码。详见 [docs/licensing.md](docs/licensing.md) 和 [docs/provenance.md](docs/provenance.md)。

## 当前器件与缺口

**已有：**

- **PTK7452MG 180° PWM 舵机 ×8**（v0 只用 2 个，其余 6 个备用）
- **ESP32-S3 无源直连转接板 ×1**（ESP32-S3 直插；GPIO→3-pin；共用 V+/GND；级联；**没有 PCA9685**）
- ESP32-S3 开发板 ×1（确认具体型号/USB-C/可用 GPIO）
- Juxi 6 轴 IMU ×1（I²C `0x23`、100 kHz、3.3V、上电等 5 s）

**还需要（详见 [bom/bom.md](bom/bom.md)）：**

- **6V/5A 舵机电源**（B 线关键；不是旧的 5V/3A）、1000–2200 µF、5A 保险丝、电源开关、USB-C 数据线
- B 线 3D 打印件（[hardware/juxi_b_line/STL](hardware/juxi_b_line/STL)）、M2/M3 螺丝/扎带、橡胶 O 圈
- 杜邦线、舵机延长线、IMU 固定/走线
- 选配：INA219 电流检测、舵机测试仪、备用舵机
- **GPIO4–18 ↔ CH1–CH8 实际映射待你口述后填入 [docs/pinmap.md](docs/pinmap.md) 和 `config.h`**

## 目录结构

```
SR-Support/
├─ README.md
├─ LICENSE                     # 当前 proprietary；开源前先看 licensing.md
├─ docs/                       # 文字内容（只放 Markdown）
│  ├─ b-line.md                # 当前 B 线决定/硬件/风险/重训计划
│  ├─ requirements.md          # 工程需求
│  ├─ pinmap.md                # B 线引脚（待口述）
│  ├─ licensing.md             # 许可/来源规则（商用必读）
│  ├─ provenance.md            # 来源记录
│  ├─ applications.md          # 应用场景
│  └─ hardware-validation.md   # 机械验证清单
├─ bom/                        # B 线 BOM
├─ firmware/
│  ├─ sr_support_b_ptk/        # 当前主固件：Juxi B 线 + PTK7452（PWM）
│  ├─ sr_support_2dof/         # 旧 8 路/waypoint 骨架（保留用于手动/8 路测试）
│  └─ imu_module_i2c_test/     # Juxi IMU 读取测试
├─ training/
│  └─ b_line/                  # B 线 MuJoCo/Gym/PPO 训练/评估/导出（PTK7452）
├─ hardware/
│  └─ juxi_b_line/             # B 线 CAD/STL/STEP（CERN-OHL-S-2.0）
├─ tools/                      # 旧 8 路串口整定/日志工具
├─ third_party/juxi-2dof/      # Juxi 上游许可/NOTICE
└─ assets/                     # 图片/下载资料
```

## 快速开始（B 线）

> 第一次做请直接按 **[docs/build-guide.md](docs/build-guide.md)** 从阶段 0 走到阶段 12；下面只是索引。

1. **打印/装配**：当前实机是 SelfRisingRobot 的 3D 打印件（`footP/arm1P/arm2P/armhornP×2`，见 `D:\Project\3D-Models\self-rising-robot`）；先量 PTK7452 实物：23.6×26.9×11.7 mm、25T、1520 µs 中位。Juxi B 线 STL 仍保留在 [hardware/juxi_b_line/STL](hardware/juxi_b_line/STL) 作为备选结构。
2. **先跑 IMU**：ESP32-S3 + Juxi IMU，烧 [`imu_module_i2c_test.ino`](firmware/imu_module_i2c_test/imu_module_i2c_test.ino)，确认 0x23/100kHz/3.3V、方向。
3. **舵机空载**：**6V/5A** + 1000–2200 µF，单个/两个发 1520/500/2500 µs，测方向、电流、6V 跌落；校准中位。
4. **烧 B 线固件**：[`firmware/sr_support_b_ptk/`](firmware/sr_support_b_ptk/)；上电默认保持；`t` 自检方向，`s` 停止并保持，`x` 释放 PWM，`r` 重新初始化，`g` 跑策略。
5. **基线试跑**：手扶机器人摆成倒地姿态，低预期地用 `include/policy_b.h`（PTK7465 128×128）确认动作方向；**不要直接放手**。
6. **重训**：按 [training/b_line/README.md](training/b_line/README.md)。仿真模型已按你的 SelfRisingRobot 打印件生成；先称重并把 `tools/build_selfrising_model.py` 里的 `MASS_*` 改成实测值，重跑生成 `assets/robot_selfrising.xml`，再训练 128×128（逐面教师+蒸馏更稳），导出覆盖 `policy_b.h`。
7. **实机评估**：`training/b_line/evaluate.py --dr --per-face`；实机先按 8/10 目标，不要按 Juxi 的 96% 宣传。

## 重要提醒

- **PTK7452MG**：180° PWM、金属齿、约 12.2 g、25T；官方 2.8/3.4/4.5 kg·cm @4.8/6/7.4V。B 线训练按 **6V 3.4 kg·cm** 建；7.4V 约 4.5，但发热/电流要实测。
- **B 线 180° + 无位置反馈**：Juxi B 线 DR 只有 63%；PTK7452 6V 更弱，先按保守目标。确保机械无干涉；保留 `x`/电源开关。
- **质量 gap**：SelfRisingRobot 仿真整机按 **97.4 g**（打印件 51 g + 舵机 24.4 g + 电控 22 g）建；打印后**逐件称重并改 `tools/build_selfrising_model.py` 的 `MASS_*`**，重新生成 XML 再训练，否则仿真成功率不可信。
- **转接板**：无源直连/级联，B 线只用 CH1/CH2（示例 GPIO4/5）；确认每个级联口的 V+/GND/信号顺序，插反会烧。
- **电源**：6V/5A 独立；ESP32 USB-C 5V 单独供电；共地；不要用 5V/3A 或电脑 USB 带两个舵机。
- **许可**：B 线代码 MIT/Apache；CAD CERN-OHL-S（强互惠）；B 线固件无 GPL。商用前让法务确认 CERN 义务；专利 CN109693729A/B 仍需 FTO。
- **基线策略**：`policy_b.h` 是 PTK7465 策略，仅 bring-up；最终必须重训。

## 资料与许可

- 上游 B 线：[Juxi-Technology/2dof-selfrighting-robot](https://github.com/Juxi-Technology/2dof-selfrighting-robot) — 代码 MIT/Apache，硬件 CERN-OHL-S；本项目的许可/来源见 [third_party/juxi-2dof](third_party/juxi-2dof)。
- 仅参考、不可直接商用：[SelfRisingRobot](https://github.com/homemadegarbage/SelfRisingRobot) — 无许可证；本项目的 B 线训练不使用它的代码/waypoint。
- 专利：CN109693729A/B（上海电机学院，两个舵机 + 两个支撑架）；商用前做 FTO。
- 本项目许可：根目录 [`LICENSE`](LICENSE)（当前 proprietary）；依赖/来源见 [docs/licensing.md](docs/licensing.md)、[docs/provenance.md](docs/provenance.md)。

## 下一步

- [ ] 确认转接板 GPIO4–18 ↔ CH1–CH8 实际映射、级联口顺序；更新 [docs/pinmap.md](docs/pinmap.md) 和 `config.h`
- [ ] 确认 PTK7452 花键/中位/尺寸；6V/5A 电源到货
- [ ] 打印 B 线 PETG 件，称重、量尺寸
- [ ] 烧 B 线固件，IMU/`t` 自检/`s`/`x`/`r` 验证
- [ ] 用基线 `policy_b.h` 手扶试跑，确认方向
- [ ] 按实际质量/力矩重训 128×128，导出 `policy_b.h`
- [ ] 实机 100 次，记录成功率/电流/温度/齿轮
- [ ] 商用前：CERN/GPL/专利 FTO 复核

---

固件/策略未经实机验证；首次上电请手扶、空载、逐级验证，避免舵机堵转、电源倒灌和机械伤害。
