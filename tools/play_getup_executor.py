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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", default=None, help="model XML (default: b39)")
    ap.add_argument("--v1-refs", action="store_true",
                    help="use the sim v1 reference set (getup_reference_v1)")
    ap.add_argument("--hold-settle", action="store_true",
                    help="servos hold q=0 while the pose settles (legacy)")
    args = ap.parse_args()
    env = B39GetupEnv(xml_path=args.xml, limp_settle=not args.hold_settle)
    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        cycle = 0
        while viewer.is_running():
            cycle += 1
            for k, requested in enumerate(POSES):
                if not viewer.is_running():
                    return
                obs, _ = env.reset(options={"pose": requested})
                # re-center the camera on the robot for every pose so the
                # demo stays watchable even if the view was dragged away
                viewer.cam.lookat[:] = (0.0, 0.0, 0.05)
                viewer.cam.distance = 0.55
                viewer.cam.azimuth = 135
                viewer.cam.elevation = -20
                sync_sleep(viewer)
                time.sleep(1.0)
                up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
                pose = pose_from_up(float(up_vec[0]), float(up_vec[1]))
                print(f"--- cycle {cycle} pose {k + 1}/4 requested={requested} "
                      f"actual={pose} up=({up_vec[0]:+.2f},{up_vec[1]:+.2f},"
                      f"{up_vec[2]:+.2f})", flush=True)
                ex = GetupExecutor(pose, q0=env.target)
                if args.v1_refs:
                    from training.b_line.getup_reference_v1 import SEQUENCES_V1
                    seq = np.asarray(SEQUENCES_V1[pose], dtype=float)
                    ex.sequence = seq
                    ex.support = seq[-2]
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
