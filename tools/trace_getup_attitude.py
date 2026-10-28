"""Trace attitude during a reference run to tune the re-plan rule."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor, pose_from_up


def trace(pose, max_steps=400):
    env = B39GetupEnv(fallen_poses=(pose,))
    obs, _ = env.reset(options={"pose": pose})
    ex = GetupExecutor(pose, max_switches=0)
    print(f"--- {pose} ---")
    print(" tick phase up_x up_y up_z |w| class    ok")
    for t in range(max_steps):
        up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
        w = float(np.linalg.norm(env.data.qvel[3:6]))
        cls = pose_from_up(float(up_vec[0]), float(up_vec[1]))
        if t % 5 == 0:
            print(f" {t:4d} {ex.phase:5d} {up_vec[0]:+.2f} {up_vec[1]:+.2f} "
                  f"{up_vec[2]:+.2f} {w:4.1f} {cls:9s}")
        obs, _, term, trunc, info = env.step(ex.action(env, obs))
        if term or trunc:
            print(f" end t={t} ok={info.get('goal_pose')} upz={info.get('upright'):+.2f}")
            break
    env.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    for pose in (("roll_neg", "roll_pos", "pitch_pos", "pitch_neg")
                 if which == "all" else (which,)):
        trace(pose)
