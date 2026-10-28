"""Executor re-planning test: start with a wrong reference, expect recovery.

The hardware failure mode: a pitch attempt cannot lift the body and rolls the
robot onto its side. The executor must notice the pose change and re-plan to
the reference of the new lying pose. This test starts every canonical pose
with every (mostly wrong) initial reference and requires the executor to
switch and still stand the robot up.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor, pose_from_up

POSES = ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg")


def run(pose, start_pose, max_steps=700):
    env = B39GetupEnv(fallen_poses=(pose,))
    obs, _ = env.reset(options={"pose": pose})
    up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
    actual = pose_from_up(float(up_vec[0]), float(up_vec[1]))
    ex = GetupExecutor(start_pose)
    info = {}
    for _ in range(max_steps):
        obs, _, term, trunc, info = env.step(ex.action(env, obs))
        if term or trunc:
            break
    ok = bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50
    up = float(info.get("upright", -9.0))
    env.close()
    return ok, up, actual, ex


def main():
    rows = []
    print(f"{'robot':10s} {'start seq':10s} {'actual':10s} ok    up    "
          f"switches->")
    for pose in POSES:
        for start_pose in POSES:
            ok, up, actual, ex = run(pose, start_pose)
            rows.append((pose, start_pose, ok))
            print(f"{pose:10s} {start_pose:10s} {actual:10s} {str(ok):5s} "
                  f"{up:+.2f} {ex.switches} ({ex.pose})", flush=True)
    ok_n = sum(r[2] for r in rows)
    print(f"\nSWITCH TEST: {ok_n}/{len(rows)} ok")
    for r in rows:
        if not r[2]:
            print(" FAIL", r)


if __name__ == "__main__":
    main()
