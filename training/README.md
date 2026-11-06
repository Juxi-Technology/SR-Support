# training — 仿真与训练（B 线）

> **当前唯一训练目录：[`b_line/`](b_line/)**（MuJoCo + Gymnasium，参考序列执行器 + PPO）。
> 旧 6 维骨架（`env_sr_2dof.py`/`train_ppo.py` 等）已随 2026-11 瘦身移除。

配套：模型文件在 [`../hardware/v1/`](../hardware/v1/)（`robot_v1.xml` + `meshes/`），
与实机同源；文本说明见 [`b_line/README.md`](b_line/README.md)。

## 常用命令

```bash
pip install -r training/b_line/requirements.txt

# 回放/验证四姿态扶正（MuJoCo 窗口）
.venv/Scripts/python.exe tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml

# 训练（导出覆盖 firmware/sr_support_b_ptk/include/policy_b.h 后重新烧录）
.venv/Scripts/python.exe training/b_line/train.py
```

训练/评估/导出的细节与参数见 [`b_line/README.md`](b_line/README.md)。
来源与许可：[`../docs/licensing.md`](../docs/licensing.md)、[`../docs/provenance.md`](../docs/provenance.md)。
