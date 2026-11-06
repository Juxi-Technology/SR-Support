# Hardware / 模型文件

**找 3D 模型和 MuJoCo XML 看这里。**

```
hardware/
├─ README.md
└─ v1/                       # 当前在用模型（自研设计，CERN-OHL-S-2.0）
   ├─ robot_v1.xml           # MuJoCo 主模型（仿真与实时镜像共用）
   └─ meshes/                # 6 个 STL（打印件）+ 属性/质量表
      ├─ foot_bottom.stl     # 底座底板
      ├─ foot_shell.stl      # 底座外壳
      ├─ foot_servo_shoulder.stl  # 肩舵机座
      ├─ arm1_bracket.stl    # 上臂支架
      ├─ arm1_servo_elbow.stl # 肘舵机座
      ├─ arm2_strut.stl      # 小臂杆
      ├─ props.json          # 几何/质量属性
      └─ print_mass_model.json  # 逐件打印质量（15% 填充）
```

说明：

- 当前设计可组装为 **4 组装配件**（底座＝底板+外壳+肩座；上臂＝支架+肘座；小臂；舵机摇臂沿用舵机自带），
  舵机（PTK7452MG 23.6×26.9×11.7 mm、25T）为外购件，模型中以简化体表示；
- `robot_v1.xml` 是 **MuJoCo MJCF**（非 URDF）；网格由 `meshes/` 提供（XML 内 `meshdir="meshes"`），
  仿真、`tools/live_twin.py`、训练共用这一份；
- 打印参数：PETG/PLA、层高 0.2 mm、4 圈壁；打印后逐件称重，更新 `print_mass_model.json`
  与 XML 中的质量参数；
- 许可：v1 模型为自研设计，**CERN-OHL-S-2.0**；Juxi B 线旧 CAD、SelfRisingRobot STL 副本
  均已随 2026-11 瘦身从仓库移除，不再分发。

许可与使用说明见 [`../tutorial/zh-hans/11-reference.md`](../tutorial/zh-hans/11-reference.md) 与根目录 `LICENSE`。
