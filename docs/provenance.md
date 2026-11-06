# 来源记录（Provenance）

> 注（2026-11 瘦身）：文中出现的 `hardware/juxi_b_line/`、`bom/`、`firmware/sr_support_2dof/`、旧仿真模型与变体 XML 已从仓库移除，相关描述仅作历史记录；当前模型见 [`hardware/v1/`](../hardware/v1/)。

> 目的：记录本项目每个文件/组件的来源与许可，避免把无许可证内容带进商用产品。  
> 规则见 [`licensing.md`](licensing.md)。  
> 2026-10-20：主方案改为 **B 线**，复用 Juxi-Technology/2dof-selfrighting-robot `main` @ `6caaf9b` 的 MIT/Apache 代码与 CERN-OHL-S 硬件。详细文件清单见 [`../third_party/juxi-2dof/ORIGIN.md`](../third_party/juxi-2dof/ORIGIN.md)。
>
> 2026-10-22：按用户指示，MuJoCo 模型改为用户正在装配的 **SelfRisingRobot 3D 打印件**（用户本地副本 `D:\Project\3D-Models\self-rising-robot\source`）。STL 仅用于本地仿真，**不随产品/公开仓库分发**；SelfRisingRobot 无许可证，商用前必须取得许可或自行重画。代码/权重/waypoint/奖励函数仍未使用。

## 1. 本项目文件

| 路径 | 来源 | 许可证 | 说明 |
|---|---|---|---|
| `firmware/sr_support_b_ptk/*` | 基于 Juxi-Technology/2dof-selfrighting-robot B 线固件 | **MIT OR Apache-2.0** | 本地修改：PTK7452 参数、LEDC 2.x/3.x、`x`/`r` 命令；见 `third_party/juxi-2dof/` |
| `firmware/sr_support_b_ptk/include/policy_b.h` | Juxi B 线 PTK7465 策略 | **MIT OR Apache-2.0**（上游） | **仅 bring-up 基线**；PTK7452 最终策略由本项目重训 |
| `training/b_line/*` | 基于 Juxi B 线 `sim/`（`selfright_env.py`、`train.py`、`evaluate.py`、`export_policy.py`、`pretrain_teachers.py`、B 线 MJCF） | **MIT OR Apache-2.0** | 本地修改：PTK7452 力矩/质量、路径、128×128 默认、多机型支持；未复制 `expert_test.py`/`pretrain_scripted.py` |
| `training/b_line/assets/robot_ptk7452.xml` | 基于 Juxi `sim/robot_ptk7465.xml` | **MIT OR Apache-2.0** | Juxi B 线几何，保留作对照；forcerange 0.333 N·m |
| `training/b_line/assets/selfrising/*.stl` | 用户本地 SelfRisingRobot 3D 模型（`3D-Models/self-rising-robot`） | **无许可证（保留所有权利）** | **仅本地仿真用，禁止再分发**；舵机网格来自 `3D-Models/servo-ptk7452mg`（按厂商图纸自建） |
| `training/b_line/assets/robot_selfrising.xml` | `tools/build_selfrising_model.py` 生成 | 同上（几何）；生成脚本本项目编写 | 5 个打印件 + 2 台 PTK7452MG + 电控盒；质量/惯量由网格体积计算 |
| `hardware/juxi_b_line/*` | Juxi B 线 `cad/STL/b_*`、`cad/STEP/b_*`、`cad/src/b_*`、`cad/checks/*` | **CERN-OHL-S-2.0** | 未修改几何；PTK7452 与 PTK7465 壳体接近，打样前量实物 |
| `firmware/sr_support_2dof/*` | 本项目独立编写（旧 8 路/waypoint 骨架） | 见根目录 `LICENSE` | 保留用于手动/8 路测试；不是当前主方案 |
| `firmware/imu_module_i2c_test/*` | 本项目独立编写 | 同上 | 基于 Juxi 内部协议读寄存器 |
| `firmware/reference_*/*` | 本项目独立编写 | 同上 | 早期参考骨架 |
| `tools/*` | 本项目独立编写 | 同上 | 串口整定/绘图、MuJoCo 截图、模型生成 |
| `docs/*` | 本项目整理 | 同上 | 含对上游的摘要/引用；未大段复制 |
| `third_party/juxi-2dof/*` | Juxi 上游 LICENSE/NOTICE | MIT/Apache/CERN/GPL 文本（按组件） | 仅许可/来源文本，不含上游 GPL 代码 |

## 2. 第三方依赖

| 依赖 | 版本/范围 | 许可证 | 用途 | 是否修改 |
|---|---|---|---|---|
| Arduino-ESP32 core | 2.x/3.x | LGPL-2.1 | 编译/运行 | 否 |
| PlatformIO espressif32 | 未锁定 | Apache-2.0（平台） | 构建 | 否 |
| MuJoCo | >=3.1,<4 | Apache-2.0 | 仿真 | 否 |
| Gymnasium | >=0.29,<2 | MIT | 环境接口 | 否 |
| Stable-Baselines3 | >=2.3,<3 | MIT | PPO | 否 |
| PyTorch | >=2.0 | BSD-3-Clause | 训练 | 否 |
| NumPy | >=1.24 | BSD-3-Clause | 数值计算 | 否 |
| tqdm | >=4.66 | MPL-2.0 / MIT | 进度条 | 否 |
| Feetech SCServo | 上游 A 线 vendored | GPL-3.0 | **本项目 B 线不使用** | 否 |

## 3. 明确未使用/未复制的内容

来自 [SelfRisingRobot](https://github.com/homemadegarbage/SelfRisingRobot)（**无许可证**），本项目**未复制、未修改、未打包**：

- 源代码（Arduino/PlatformIO、Python、训练脚本）
- MuJoCo 模型/场景文件（`RL/robo1.xml`、`robo1_env.py` 等仅阅读参考）
- 训练好的策略权重 `policy_network.h` / `robo1_getup_ppo.zip`
- waypoint/标定参数/奖励权重（`getup_reference.py`、`scripted_getup.py` 未复制）
- README/图片/视频等文档素材

**例外（2026-10-22，用户指示）**：`training/b_line/assets/selfrising/*.stl` 是用户本地 SelfRisingRobot 3D 打印件的 STL 副本，仅用于仿真用户自己的实机。它们：

- 不进入固件、不随产品出货、不对外分发；
- 仍然没有许可证；商用/开源前必须取得作者书面许可，或按实测尺寸自行重画；
- 由 `tools/build_selfrising_model.py` 重新居中/缩放并计算惯量，未改动零件几何。

另外，Juxi 上游的 `sim/expert_test.py` 和 `sim/pretrain_scripted.py` 含 SelfRisingRobot 的 waypoint 数值；**本项目没有复制这两个文件**。  
`policy_b.h` 是 Juxi 的基线策略，可能受上游训练数据影响；它**只用于接线/台架 bring-up**，最终策略由本项目从零训练（逐面教师/PPO，不使用上述 waypoint）。

## 4. 新增文件检查清单

- [ ] 代码是否为独立编写，或来自 MIT/Apache 且保留 NOTICE？
- [ ] MJCF/STL/图片/文档是否有明确来源和许可证？
- [ ] 是否引入 GPL（B 线固件不应链接 SCServo）？
- [ ] 是否使用了 SelfRisingRobot 的代码/STL/waypoint/权重？
- [ ] CERN-OHL-S 硬件是否保留许可并评估分发义务？
- [ ] 是否涉及专利特征？是否需要 FTO 复查？
