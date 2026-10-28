# Upstream origin — Juxi-Technology/2dof-selfrighting-robot

| 项目 | 内容 |
|---|---|
| 仓库 | https://github.com/Juxi-Technology/2dof-selfrighting-robot |
| 分支/commit | `main` @ `6caaf9b`（2026-10-20 克隆时的 HEAD） |
| 代码许可 | MIT OR Apache-2.0（`sim/`、`firmware/src/`、`firmware/include/`、`cad/src/`、`tools/`） |
| 硬件许可 | CERN-OHL-S-2.0（`cad/STEP/`、`cad/STL/`） |
| 第三方 | Feetech SCServo GPL-3.0（仅 A 线使用；本项目 B 线未复制/未链接） |

## 本项目复制的文件

- `firmware/src/main.cpp` → `firmware/sr_support_b_ptk/src/main.cpp`
- `firmware/src/servo_backend.h` → `firmware/sr_support_b_ptk/src/servo_backend.h`
- `firmware/src/servo_pwm.cpp` → `firmware/sr_support_b_ptk/src/servo_pwm.cpp`
- `firmware/include/config.h` → `firmware/sr_support_b_ptk/include/config.h`（重写为 B 线/PTK7452）
- `firmware/include/policy_ptk7465.h` → `firmware/sr_support_b_ptk/include/policy_b.h`（基线，待重训）
- `firmware/platformio.ini` → `firmware/sr_support_b_ptk/platformio.ini`（改为单一 ptk7452 环境）
- `sim/selfright_env.py`、`sim/train.py`、`sim/evaluate.py`、`sim/export_policy.py`、`sim/pretrain_teachers.py` → `training/b_line/`
- `sim/robot_ptk7465.xml` → `training/b_line/assets/robot_ptk7452.xml`（改 PTK7452 力矩/质量）
- `tools/policy_stdin.c` → `training/b_line/policy_stdin.c`
- `cad/STL/b_*`、`cad/STEP/b_*`、`cad/src/b_*`、`cad/checks/*` → `hardware/juxi_b_line/`
- `LICENSE`、`NOTICE.md`、`LICENSES/MIT.txt`、`LICENSES/Apache-2.0.txt` → `third_party/juxi-2dof/`
- `LICENSES/CERN-OHL-S-2.0.txt` → `hardware/juxi_b_line/LICENSE-CERN-OHL-S-2.0.txt`

## 本地修改

- PTK7452MG：3.4 kg·cm @6V（0.333 N·m）、12.2 g、1520 µs、500–2500 µs。
- 固件：LEDC core 2.x/3.x 兼容；`IMU_STARTUP_MS=5000`；新增 `x`（释放 PWM）、`r`（重新初始化）。
- 训练：默认 `ptk7452`、128×128、Windows `DummyVecEnv`、路径改为 `training/b_line/`。
- 配置：GPIO4/5、I²C 8/9、6V/5A、无 PCA9685。
- 未复制 `sim/expert_test.py`、`sim/pretrain_scripted.py`（含 SelfRisingRobot waypoint 数值）。
- `policy_b.h` 仅为 PTK7465 基线；最终由本项目按 PTK7452/实际质量重训。

## 保留义务

- 保留 MIT/Apache 版权与许可声明；修改处注明。
- 硬件 CAD/STL/STEP 按 CERN-OHL-S-2.0 使用；分发/修改前确认互惠义务。
- 不要把 SelfRisingRobot 的代码/STL/waypoint 带入本项目。
