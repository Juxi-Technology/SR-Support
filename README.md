# SR-Support

低成本主动自扶正装置：任一方向倾倒后，依靠一只 2-DOF 手臂（肩 + 肘）撑地、按压、撬起，
**四方向直接起身（约 1–6 秒）**。主控 ESP32-S3 + Juxi 6 轴 IMU + 2× PTK7452MG（180° PWM）。

> **当前状态（2026-11）**：四方向自扶正实机验证通过（参考序列执行器，无需翻滚）；
> 支持 WiFi 状态页/配网/MuJoCo 无线实时镜像；方向键零点校准工具（`z` 命令）；
> IMU 陀螺+加速度计零点标定（NVS 持久化）。成品出厂已组装、标定、测试。

## 从这里开始

| 你想做什么 | 看这里 |
|---|---|
| **教程（唯一文档入口，按阅读顺序）** | [`tutorial/zh-hans/`](tutorial/zh-hans/index.md)（英文版 [`en/`](tutorial/en/index.md)） |
| **3D 模型 / MuJoCo XML** | [`hardware/v1/`](hardware/v1/)（`robot_v1.xml` + `meshes/`） |
| 固件（命令表、镜像、零点、WiFi） | [`firmware/sr_support_b_ptk/README.md`](firmware/sr_support_b_ptk/README.md) |
| 电脑端工具 | [`tools/README.md`](tools/README.md) |
| 仿真与训练 | [`training/README.md`](training/README.md) |
| 许可与来源（商用必读） | [`tutorial/zh-hans/11-reference.md`](tutorial/zh-hans/11-reference.md)（11.5 节） |

## 目录结构

```
SR-Support/
├─ tutorial/                # 教程（zh-hans / en，按阅读顺序 12 页，含目录）
├─ firmware/
│  ├─ sr_support_b_ptk/     # ★ 当前主固件
│  ├─ i2c_scanner/          # IMU 地址诊断
│  ├─ servo_center_ptk/     # 装配中位辅助
│  ├─ servo_test_ptk/       # 舵机单路测试
│  └─ imu_module_i2c_test/  # IMU 读取测试
├─ hardware/v1/             # ★ 当前模型：robot_v1.xml + meshes（STL）
├─ training/b_line/         # 仿真/训练/评估/导出（与实机同源模型）
├─ tools/                   # 镜像、零点工具、监控、日志
└─ third_party/juxi-2dof/   # 上游代码许可/NOTICE（合规保留）
```

## 快速开始（成品用户）

1. 直立上电，串口出现 `ready; send g to run`；
2. 把机器人放倒（任意方向），**松手静止约 0.5 秒**，自动扶正开始；
3. 可选 WiFi：连热点 `SR-Support`（密码 `srsupport`）→ 打开 `http://192.168.4.1`
   （状态页 + 配网 + Twin 流开关）；
4. MuJoCo 实时镜像：`.venv/Scripts/python.exe tools/live_twin.py --tcp <Robot IP>:3333`
   （工具环境安装见教程 02 页；不想用虚拟环境就把 `.venv/Scripts/python.exe` 换成 `python`）。

自组装流程（环境→打印→装配→烧录→标定）见 [`tutorial/zh-hans/index.md`](tutorial/zh-hans/index.md)。

## 重要提醒

- **电源**：舵机规格 6 V / ≥5 A（独立供电）；5 V 可用但堵转扭矩约降 15%，
  `roll_neg` 更依赖楔形泵。ESP32 用 USB-C 单独供电，与舵机电源共地，**不要把 6 V 接到 ESP32**；
- **IMU 标定**：更换/重装 IMU 后，站立水平发 `c`（陀螺+加速度计零点，写入 NVS）；
- **零点**：换齿/重装舵盘后用 `tools/hw_shoulder_range.py` 定零并固化（教程第 06 页）；
- **许可**：代码 MIT/Apache-2.0；自研 CAD/模型 CERN-OHL-S-2.0；SelfRisingRobot 无许可、
  仓库不包含其任何文件；专利 CN109693729A/B 商用前需 FTO。详见
  教程 [`11-reference`](tutorial/zh-hans/11-reference.md) 的许可一节。

## 资料与许可

- 上游 B 线：[Juxi-Technology/2dof-selfrighting-robot](https://github.com/Juxi-Technology/2dof-selfrighting-robot)
  — 代码 MIT/Apache，硬件 CERN-OHL-S；许可见 [`third_party/juxi-2dof/`](third_party/juxi-2dof/)；
- 仅参考、不可直接商用：[SelfRisingRobot](https://github.com/homemadegarbage/SelfRisingRobot)（无许可证）；
- 本项目许可：根目录 [`LICENSE`](LICENSE)；来源记录见 [`third_party/juxi-2dof/ORIGIN.md`](third_party/juxi-2dof/ORIGIN.md) 与 git 历史。
