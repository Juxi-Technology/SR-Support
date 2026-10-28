"""Arm-mass sensitivity of the roll_neg reference.

Hardware signature: instead of yawing the lying body toward the pitch axis
(as the sim does), the arm sweeping over the top rolls the body over its top
(up_z goes strongly negative) and the sequence ends kneeling. Test whether a
heavier arm reproduces that in sim.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor


def run(pose, arm_scale, max_steps=400):
    env = B39GetupEnv(fallen_poses=(pose,))
    m = env.model
    for name in ("arm1", "arm2"):
        bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
        m.body_mass[bid] *= arm_scale
        m.body_inertia[bid] *= arm_scale
    obs, _ = env.reset(options={"pose": pose})
    ex = GetupExecutor(pose, max_switches=0)
    up_hist = []
    info = {}
    for t in range(max_steps):
        up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2].copy()
        up_hist.append(up_vec)
        obs, _, term, trunc, info = env.step(ex.action(env, obs))
        if term or trunc:
            break
    ups = np.array(up_hist)
    min_upz = float(ups[:, 2].min())
    max_abs_ux = float(np.abs(ups[:, 0]).max())
    yaw = math.degrees(math.atan2(ups[-1][1], ups[-1][0]))
    ok = bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50
    print(f"{pose} arm x{arm_scale:.1f}: ok={ok} up_final={np.round(ups[-1], 2)} "
          f"min_upz={min_upz:+.2f} max|up_x|={max_abs_ux:.2f} "
          f"final_yaw={yaw:+.0f}deg steps={env.step_count}", flush=True)
    env.close()


def main():
    for scale in (1.0, 1.5, 2.0, 2.5):
        run("roll_neg", scale)
    for scale in (1.0, 2.0):
        run("roll_pos", scale)


if __name__ == "__main__":
    main()
