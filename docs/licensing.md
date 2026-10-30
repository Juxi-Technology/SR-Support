# 许可与净室实现方案

> 本文是工程/合规建议，不是法律意见；商用前请律师/专利代理人复核。  
> 结论先说：**SelfRisingRobot 没有许可证，默认是“保留所有权利”，不能把它的代码、STL、训练权重、waypoint 直接用于商用产品或再分发。**  
> 但“用两个舵机推地起立”“用 MuJoCo + PPO 训练”这类**方法/思路**本身不受版权保护。对 **SelfRisingRobot** 我们采用**独立重写**；对 **Juxi B 线**（MIT/Apache）按许可复用并保留 NOTICE。详见第 0 节。

---

## 0. 2026-10-20 B 线决定后的许可结论

- 主方案改为 **B 线**（PTK7452MG 180° PWM），技术基座复用 **Juxi-Technology/2dof-selfrighting-robot**：
  - 软件/仿真：**MIT OR Apache-2.0**；
  - 硬件 CAD/STL/STEP：**CERN-OHL-S-2.0**（强互惠，不是 MIT）；
  - A 线固件才链接 **GPL-3.0** 的 Feetech SCServo；**B 线固件不链接**。
- 这不是“净室重写”，而是**合规复用**：保留 `third_party/juxi-2dof/` 的 LICENSE/NOTICE，修改处标注来源。  
- 对 **SelfRisingRobot（无许可证）**仍执行第 2/3/4 节的“不复制”规则；B 线训练也不使用它的 waypoint/代码。  
- `policy_b.h` 当前是 Juxi 的 **PTK7465 基线策略**，只用于接线/台架；最终策略由本项目按 PTK7452/实际质量重训。  
- **2026-10-22 更新**：仿真几何改为用户实机的 **SelfRisingRobot 3D 打印件**（`training/b_line/assets/selfrising/`）。这是用户本地副本，**仅用于仿真自有实机，不随产品/公开仓库分发**；SelfRisingRobot 无许可证，商用前仍需作者书面许可或按实测尺寸自行重画。代码、权重、waypoint、奖励函数仍未使用。
- **2026-10-30 更新**：v1 版（`training/b_line/assets/robot_v1*.xml` + `v1_meshes/`）为**自研设计**（由自有 FreeCAD/STEP 件转换），不含第三方几何，随仓库以 **CERN-OHL-S-2.0** 发布；2026-10-22 条目的 selfrising 资产规则不变。
- 商用前仍需：CERN-OHL-S 义务确认、Arduino LGPL 评估、专利 FTO。

---

## 1. 三条可选路线

| 路线 | 做法 | 成本 | 风险 | 建议 |
|---|---|---|---|---|
| **A. 净室自研** | 只借鉴公开的方法/论文/功能描述；代码、MJCF、奖励函数、waypoint、STL 全部自己写/自己整定/自己训练 | 开发工作量中等 | 低（版权）；仍需专利 FTO | 对 **SelfRisingRobot** 仍推荐 |
| B. 向作者取得商业许可 | 联系作者，签书面许可，明确代码/STL/权重/衍生作品/再分发/收费 | 谈判+许可费 | 作者可能不回复或报价高 | 可作为并行选项；在拿到书面许可前不要用 |
| **C. 基于 MIT/Apache/CERN 项目（当前 B 线）** | 复用 Juxi-Technology/2dof-selfrighting-robot B 线（软件 MIT/Apache，硬件 CERN-OHL-S），保留 NOTICE；修改处标注 | 低 | 硬件 CERN 互惠义务；仍需 FTO | **当前采用**；与 SelfRisingRobot 的“不复制”并行 |

**当前执行路线：C（Juxi B 线复用）+ 对 SelfRisingRobot 仍走 A。**  
SelfRisingRobot 的任何文件都不进入本项目；Juxi 的 MIT/Apache 代码按许可复用，硬件按 CERN-OHL-S 处理。

### 1.1 联系作者取得许可（可选的 B 路线）

如果希望直接使用作者的代码/STL/权重，先发一封书面询问，保留回复记录。模板要点：

> 主题：Commercial license inquiry — SelfRisingRobot  
> 1. 我们是谁、产品形态、预计数量/销售区域；  
> 2. 希望使用的范围：源代码 / STL / 训练权重 / 文档（逐项列明）；  
> 3. 是否允许修改、再分发、闭源、收费；  
> 4. 许可费/版税/支持方式；  
> 5. 请对方书面确认许可范围和期限。  

在拿到明确书面许可前，按 A 路线执行；不要以“作者没回复”为由默认获得许可。

---

## 2. 哪些东西绝对不能复制

- **源代码**：`.ino` / `.cpp` / `.h` / `.py` 文件，包括注释、变量名、函数结构、状态机写法。不要“改改变量名”式复制。
- **机械文件**：`foot.stl`、`arm1.stl`、`arm2.stl`、`armhornP.stl`、STEP/DWG/F3D 等。不能打印后卖产品，也不能放进产品说明书/开源仓库。**本地用于仿真自己已购买的打印件是允许的**（`training/b_line/assets/selfrising/`），但不得再分发。
- **训练产物**：`policy_network.h`、模型权重、训练曲线、超参数文件。
- **waypoint / 标定参数**：作者调好的角度序列、阈值、奖励权重。
- **文档/图片/视频**：README 文字、截图、演示视频，不能直接用于宣传物料。
- **训练环境**：作者的 MuJoCo XML、Gym 环境、奖励函数实现。

> “GitHub 上没写 license” ≠ 公共领域。没有 license 时，默认适用著作权法，作者保留全部权利。

---

## 3. 哪些事情可以做

- 使用**抽象方法**：2-DOF 臂、倒地检测、4 种倒姿、PPO、域随机化、sim-to-real、行为克隆等。
- 阅读**论文/博客/公开演讲**，自己实现公式和流程。
- 使用**通用库**：MuJoCo、Gymnasium、Stable-Baselines3、PyTorch、NumPy 等（见第 5 节许可证）。
- **自己训练**策略：自己写 MJCF、自己定 observation/action/reward、自己跑 PPO、自己导出权重。
- **自己设计**机械件：按你的舵机尺寸、机身重心、臂长重新画 CAD/OpenSCAD。
- **自己整定** waypoint：用本项目固件的手动模式实测，记录角度。
- 使用**明确许可**的第三方素材（MIT/BSD/Apache/CC0），并保留版权声明。

---

## 4. 不复制 SelfRisingRobot + 合规复用 MIT/Apache

1. **SelfRisingRobot** 的代码/STL/权重/waypoint 一律不复制；只使用公开的抽象方法。
2. **Juxi B 线**的 MIT/Apache 代码可以复用；保留 `third_party/juxi-2dof/` 的 LICENSE/NOTICE，修改处标注来源。
3. Juxi B 线的 MJCF/仿真可以修改；`training/b_line/` 里保留来源说明。
4. `policy_b.h` 是 Juxi 的基线策略，只用于 bring-up；最终策略由本项目训练产生。
5. 不使用 SelfRisingRobot 的 waypoint；Juxi 上游的 `expert_test.py`/`pretrain_scripted.py` 未被复制。
6. 硬件：Juxi B 线 CAD/STL 按 **CERN-OHL-S-2.0** 使用；商用/分发前确认互惠义务。
7. 代码评审时检查来源；新增第三方文件必须记录许可证。
8. 记录来源：见 [`provenance.md`](provenance.md)。

### 4.1 B 线组件许可证

| 组件 | 许可证 | 商用注意 |
|---|---|---|
| `firmware/sr_support_b_ptk/`（基于 Juxi B 线） | MIT OR Apache-2.0 | 保留 NOTICE；不链接 GPL SCServo |
| `training/b_line/`（基于 Juxi B 线 sim） | MIT OR Apache-2.0 | 保留 NOTICE；未复制 SelfRisingRobot 数据 |
| `training/b_line/assets/selfrising/`（用户实机 STL） | **无许可证** | 仅本地仿真；不随产品/公开仓库分发；商用需许可或重画 |
| `hardware/juxi_b_line/`（CAD/STL/STEP） | **CERN-OHL-S-2.0** | 强互惠；分发修改后的硬件设计通常需按同许可提供源 |
| `policy_b.h`（Juxi PTK7465 基线） | MIT OR Apache-2.0（上游） | 仅 bring-up；最终重训；上游训练数据可能有 waypoint 尾巴 |
| `third_party/juxi-2dof/` | MIT/Apache + NOTICE | 不要删除 |
| Feetech SCServo | GPL-3.0 | **B 线未使用**；A 线固件才会链接 |
| SelfRisingRobot | 无许可证 | **不使用** |

> CERN-OHL-S 是硬件设计的强互惠许可（类似硬件 GPL），与 MIT/Apache 不是一回事；如果这是你们公司自己的仓库，请让法务确认是否可以重新授权，以及对外分发时的义务。

---

## 5. 依赖许可证（商用角度）

| 依赖 | 许可证 | 商用 | 注意 |
|---|---|---|---|
| Arduino-ESP32 core | **LGPL-2.1** | 可以 | 闭源固件需评估 LGPL 的“可重新链接”义务；不想有义务可改用 **ESP-IDF（Apache-2.0）**，或保留目标文件/提供重链接方式。建议商用前让法务确认。 |
| ESP-IDF | **Apache-2.0** | 可以 | 若从 Arduino 迁到 ESP-IDF，需重写 `setup/loop` 为 `app_main`，但驱动逻辑可复用。 |
| MuJoCo | **Apache-2.0** | 可以 | 训练/仿真用；保留 NOTICE。 |
| Gymnasium | **MIT** | 可以 | 训练环境接口。 |
| Stable-Baselines3 | **MIT** | 可以 | PPO 实现。 |
| PyTorch | **BSD-3-Clause** | 可以 | 训练。 |
| NumPy | **BSD-3-Clause** | 可以 | 数值计算。 |
| pyserial | **BSD-3-Clause** | 可以 | 串口调参工具。 |
| matplotlib | **PSF-based / BSD-compatible** | 可以 | 画图工具，不分发到产品即可。 |
| Juxi IMU 协议/文档 | 公司内部资料 | 内部使用 | 不要把内部 wiki 原文/图片放进公开仓库或对外文档；代码里的寄存器地址是实现必需信息。 |
| SelfRisingRobot | **无许可证** | **不可以** | 代码/权重/waypoint 不使用；STL 仅本地仿真自有实机，不再分发 |

> 固件里没有使用 `ESP32Servo` 库；B 线直接用 LEDC（旧 8 路骨架有 PCA9685 参考实现）。`Wire` 属于 Arduino-ESP32 core（LGPL-2.1）。

---

## 6. 专利是另一件事（重要）

版权净室**不解决专利**。已知：

- **CN109693729A / B**（上海电机学院）：“两个舵机 + 两个支撑架”的自扶正装置。商用前必须做 FTO（Freedom to Operate）检索/分析。
- 可能的规避方向：不同自由度/不同支撑方式/不同驱动机构/不同控制方法；但必须由专利代理人确认，不能自行判断。
- 建议：在打样前做一次中国专利检索（关键词：自扶正、不倒翁、起立、支撑臂、双舵机、复位机器人），并保留检索记录。

---

## 7. 建议的落地顺序

1. **v0 固件**：本项目自己的 2-DOF 状态机 + 手动整定；不依赖 RL，不涉及作者代码。
2. **v0 机械**：自己画/打印 2-DOF 臂；先用纸板验证。
3. **v0 waypoint**：用 `tools/sr_tune.py` 记录，填入本项目 `getup_sequence.h`。
4. **v1 可选 RL**：用本项目 `training/` 自建 MJCF + PPO 训练，导出自己的 `policy_network.h`。
5. **商用前**：FTO/专利分析、LGPL 评估、第三方依赖清单、产品认证（如适用）。

---

## 8. 一句话总结

**不要复制表达，自己产生表达；方法可以用，依赖要选可商用的；版权之外还要看专利。** 本项目当前的代码、仿真和工具都按这个原则编写。
