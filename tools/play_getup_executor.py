"""Loop demo of the reference+feedback get-up executor in MuJoCo.

The robot is placed directly in each of the four canonical lying poses in
turn (roll_pos, roll_neg, pitch_pos, pitch_neg), the executor runs until it
stands, then the robot is reset to the next lying pose. The sequence repeats
until the viewer is closed.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv
from training.b_line.getup_executor import GetupExecutor, pose_from_up

CTRL_DT = 0.02
POSES = ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg")


def sync_sleep(viewer):
    viewer.sync()
    time.sleep(CTRL_DT)


def main():
    env = B39GetupEnv()
    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        viewer.cam.lookat[:] = (0.0, 0.0, 0.10)
        viewer.cam.distance = 0.65
        viewer.cam.azimuth = 135
        viewer.cam.elevation = -18
        cycle = 0
        while viewer.is_running():
            cycle += 1
            for k, requested in enumerate(POSES):
                if not viewer.is_running():
                    return
                obs, _ = env.reset(options={"pose": requested})
                sync_sleep(viewer)
                time.sleep(1.0)
                up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
                pose = pose_from_up(float(up_vec[0]), float(up_vec[1]))
                print(f"--- cycle {cycle} pose {k + 1}/4 requested={requested} "
                      f"actual={pose} up=({up_vec[0]:+.2f},{up_vec[1]:+.2f},"
                      f"{up_vec[2]:+.2f})", flush=True)
                ex = GetupExecutor(pose)
                info = {}
                for t in range(700):
                    action = ex.action(env, obs)
                    obs, _, terminated, truncated, info = env.step(action)
                    sync_sleep(viewer)
                    if terminated or truncated:
                        break
                ok = bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50
                print(f"    executor ok={ok} up={info.get('upright', -9):+.2f} "
                      f"servo={np.round(info.get('servo_angles', []), 2).tolist()} "
                      f"steps={env.step_count}", flush=True)
                time.sleep(1.2)


if __name__ == "__main__":
    main()
