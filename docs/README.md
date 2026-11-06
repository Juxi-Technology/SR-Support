# Docs / 文字内容

本目录只放文字内容（Markdown）。教程在 [`../tutorial`](../tutorial)，代码在 [`../firmware`](../firmware)，模型/CAD 在 [`../hardware`](../hardware)，工具在 [`../tools`](../tools)，训练在 [`../training`](../training)。

- [`requirements.md`](requirements.md)：**工程需求文档（先看这个）**，定义慢速起立方案的范围、FR/NFR、硬件/软件/机械/安全/验收标准。
- [`plan.md`](plan.md)：**当前项目计划与约定**：几何/关节/方向的统一描述，阶段计划（机械拍板→仿真定稿→固件→实机校准→分级测试），以及“实机只有固定动作”的排查顺序。
- [`build-guide.md`](build-guide.md)：**客户版完整复现手册**：开箱→打印→装配→接线→IMU/舵机验证→训练→评估→实机验收，含预期输出/STOP 条件/故障排查。
- [`platformio-install.md`](platformio-install.md)：**PlatformIO 安装/烧录（Windows）**；本机已装 Core 6.2.0 + VS Code 扩展。
- [`checklist.md`](checklist.md)：一页式检查清单（可打印）。
- [`b-line.md`](b-line.md)：**当前 B 线方案决定**：PTK7452MG、无源直连转接板、复用 Juxi B 线代码/CAD、重训计划、风险。
- [`pinmap.md`](pinmap.md)：ESP32-S3 / 转接板 / 8 舵机引脚映射（B 线只用 2 路，待口述/核对）。
- [`licensing.md`](licensing.md)：**许可与净室方案**；哪些能商用、哪些不能复制、依赖许可证、专利风险。
- [`provenance.md`](provenance.md)：来源记录；证明代码/仿真/机械件为独立实现。
- [`applications.md`](applications.md)：应用场景与产品化建议。
- [`hardware-validation.md`](hardware-validation.md)：机械验证清单（纸板/假臂/转台/棍子）。

