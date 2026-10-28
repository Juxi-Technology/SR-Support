"""Random-orientation regression for the executor (seeded, reproducible)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor, pose_from_up

N = 48
SEED = 7


def random_quat(rng):
    u1, u2, u3 = rng.random(3)
    return np.array([
        math.sqrt(1 - u1) * math.sin(2 * math.pi * u2),
        math.sqrt(1 - u1) * math.cos(2 * math.pi * u2),
        math.sqrt(u1) * math.sin(2 * math.pi * u3),
        math.sqrt(u1) * math.cos(2 * math.pi * u3),
    ])  # w, x, y, z


def run(quat):
    env = B39GetupEnv(fallen_poses=("roll_pos",))
    env.data.qpos[:] = 0.0
    env.data.qvel[:] = 0.0
    env.data.qpos[0:3] = [0.0, 0.0, 0.08]
    env.data.qpos[3:7] = quat
    env.target[:] = 0.0
    env.data.ctrl[:] = 0.0
    mujoco.mj_forward(env.model, env.data)
    for _ in range(env.settle_steps):
        env.data.ctrl[:] = 0.0
        mujoco.mj_step(env.model, env.data)
    env.target[:] = 0.0
    env.data.ctrl[:] = 0.0
    env.step_count = 0
    env.success_count = 0
    env.prev_upright = env._upright()
    up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
    pose = pose_from_up(float(up_vec[0]), float(up_vec[1]))
    ex = GetupExecutor(pose)
    obs = env._obs()
    info = {}
    for _ in range(700):
        obs, _, term, trunc, info = env.step(ex.action(env, obs))
        if term or trunc:
            break
    ok = bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50
    up0 = float(up_vec[2])
    env.close()
    return ok, up0, pose, ex.switches


def main():
    rng = np.random.default_rng(SEED)
    rows = []
    for i in range(N):
        q = random_quat(rng)
        ok, up0, pose, sw = run(q)
        rows.append(ok)
        print(f"{i:2d} up0={up0:+.2f} pose={pose:9s} ok={ok} sw={sw}",
              flush=True)
    print(f"\nRANDOM: {sum(rows)}/{N} ok")


if __name__ == "__main__":
    main()
