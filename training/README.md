# training — 仿真与训练（B 线）

> **当前唯一训练目录：[`b_line/`](b_line/)**（MuJoCo + Gymnasium，参考序列执行器 + PPO）。
> 旧 6 维骨架（`env_sr_2dof.py`/`train_ppo.py` 等）已随 2026-11 瘦身移除。

配套：模型文件在 [`../hardware/v1/`](../hardware/v1/)（`robot_v1.xml` + `meshes/`），
与实机同源；文本说明见 [`b_line/README.md`](b_line/README.md)。

## 常用命令

先按教程 02 页创建并激活项目 `.venv`，然后：

```bash
pip install -r training/b_line/requirements.txt

# 回放/验证四姿态扶正（MuJoCo 窗口）
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml

```

执行器/参考序列与仿真细节见 [`b_line/README.md`](b_line/README.md)（PPO 训练管线已随 2026-11 瘦身移除）。
来源与许可：根目录 `LICENSE`、[`../third_party/juxi-2dof/`](../third_party/juxi-2dof/)、教程 10-reference。
