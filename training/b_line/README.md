# training/b_line — 仿真与回放（与实机同源模型）

> 2026-11 起本产品为**参考序列执行器方案**（无需策略训练）。本目录保留仿真环境、
> 执行器与参考序列，用于回放、验证和参数调整。
> 早期 PPO 策略训练管线（`selfright_env.py`/`train.py` 等）已随仓库瘦身移除，
> 如需要策略范式可参考上游 Juxi-Technology/2dof-selfrighting-robot（MIT/Apache-2.0）。

## 文件

| 文件 | 作用 |
|---|---|
| `getup_env.py` | MuJoCo/Gymnasium 扶正环境（默认加载 `hardware/v1/robot_v1.xml`；含躺姿落定/limp settle） |
| `getup_executor.py` | 参考+反馈执行器（与固件逐参数一致，含分段自适应保持） |
| `getup_reference_b39.py` | **当前四方向参考序列**（与固件 `EXEC_REF*` 逐值同步） |
| `getup_reference_v1.py` | v1 模型专用历史序列（记录用） |
| `requirements.txt` | Python 依赖（mujoco / gymnasium / numpy） |

## 常用命令

```bash
pip install -r training/b_line/requirements.txt

# 四姿态回放（MuJoCo 窗口）
.venv/Scripts/python.exe tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml

# 躺姿验证 + 扶正回放 + 拼图
.venv/Scripts/python.exe tools/verify_v1_lying_poses.py
```

模型/质量更新流程见 [`../../docs/build-guide.md`](../../docs/build-guide.md) §11.2
（改 `hardware/v1/meshes/print_mass_model.json` 与 `robot_v1.xml`）。
来源与许可：[`../../docs/licensing.md`](../../docs/licensing.md)。
