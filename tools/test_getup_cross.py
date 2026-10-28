"""Cross matrix: every canonical lying pose executing every reference sequence.

Purpose: on real hardware one pitch direction fails and rolls the robot onto
a side. Check in sim which sequences can recover which poses, so the executor
can hand over to a working sequence when the pose axis changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor

POSES = ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg")


def run(pose, seq_pose, max_steps=700):
    env = B39GetupEnv(fallen_poses=(pose,))
    obs, _ = env.reset(options={"pose": pose})
    ex = GetupExecutor(seq_pose)
    info = {}
    for _ in range(max_steps):
        obs, _, term, trunc, info = env.step(ex.action(env, obs))
        if term or trunc:
            break
    ok = bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50
    up = float(info.get("upright", -9.0))
    pen = float(info.get("pen", 0.0))
    steps = env.step_count
    env.close()
    return ok, up, pen, steps


def main():
    print(f"{'robot pose':10s} {'sequence':10s} ok    up     pen(mm) steps")
    for pose in POSES:
        for seq_pose in POSES:
            ok, up, pen, steps = run(pose, seq_pose)
            print(f"{pose:10s} {seq_pose:10s} {str(ok):5s} {up:+.2f} "
                  f"{pen*1000:7.1f} {steps:5d}", flush=True)


if __name__ == "__main__":
    main()
