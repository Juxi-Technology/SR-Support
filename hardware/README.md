# Hardware / CAD / STL

本目录用于存放 **CAD、STL、STEP、3D 打印文件**；机械验证清单在 [`../docs/hardware-validation.md`](../docs/hardware-validation.md)，文字方案在 [`../docs`](../docs)，许可规则在 [`../docs/licensing.md`](../docs/licensing.md)。

建议结构（**全部自行设计或使用许可明确的模型**）：

```
hardware/
├─ README.md
├─ juxi_b_line/          # 当前 B 线：Juxi B 线 CAD/STL/STEP（CERN-OHL-S-2.0）
├─ sr_2dof/              # 我们自己的旧 2-DOF/8 路结构（如继续做）
├─ drawings/             # 尺寸图、装配图、爆炸图
└─ references/           # 仅放许可明确的参考模型（MIT/CC0/商业授权），并记录来源
```

当前 B 线使用 [`juxi_b_line/`](juxi_b_line/)：b_base / b_arm1 / b_arm2，PETG 打印。  
注意：Juxi B 线 CAD 是 **CERN-OHL-S-2.0**（强互惠硬件许可），不是 MIT；商用/分发前确认义务，见该目录 README。

注意：

- **不要**把 SelfRisingRobot 的 `foot.stl`、`arm1.stl`、`arm2.stl`、`armhornP.stl` 放进本目录用于商用；该项目无许可证，默认保留所有权利。个人学习也要注明来源，商用/再分发前联系作者。
- 打印前先确认 PTK 7452MG 的尺寸（23.6×26.9×11.7 mm）和输出花键（常见 25T）；舵盘/连杆按实物测绘。
- 先用纸板/木条验证力臂和接触点，再打印最终件；不要直接把未验证的 STL 当成品。
- 每个新增 CAD/STL 在 [`../docs/provenance.md`](../docs/provenance.md) 记录来源/许可证。
