"""Hardware-like handover test.

On hardware the pitch attempt fails and tips the robot onto its side while the
arm is parked at the previous sequence's support waypoint (0, +-1.55). This
checks that the roll references still stand the robot up from that state,
starting from the current joint target (as the firmware switch does).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor, pose_from_up


def run(pose, arm0, max_steps=700):
    env = B39GetupEnv(fallen_poses=(pose,))
    obs, _ = env.reset(options={"pose": pose})
    env.target[:] = arm0
    env.data.qpos[[int(env.model.jnt_qposadr[j]) for j in env.servo_jids]] = arm0
    env.data.qvel[:] = 0.0
    env.data.ctrl[:] = arm0
    env_eq = env.settle_steps
    import mujoco
    mujoco.mj_forward(env.model, env.data)
    for _ in range(env_eq // 2):
        env.data.ctrl[:] = env.target
        mujoco.mj_step(env.model, env.data)
    up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
    actual = pose_from_up(float(up_vec[0]), float(up_vec[1]))
    ex = GetupExecutor(actual)
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
    cases = [
        ("roll_neg", np.array([0.0, 1.55])),
        ("roll_neg", np.array([0.0, -1.55])),
        ("roll_pos", np.array([0.0, 1.55])),
        ("roll_pos", np.array([0.0, -1.55])),
        ("pitch_pos", np.array([0.0, -1.55])),
        ("pitch_neg", np.array([0.0, 1.55])),
    ]
    for pose, arm0 in cases:
        ok, up, actual, ex = run(pose, arm0)
        print(f"{pose:10s} arm0=({arm0[0]:+.2f},{arm0[1]:+.2f}) "
              f"actual={actual:10s} ok={ok} up={up:+.2f} switches={ex.switches}",
              flush=True)


if __name__ == "__main__":
    main()
