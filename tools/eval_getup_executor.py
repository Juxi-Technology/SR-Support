"""Evaluate the deterministic reference+feedback executor on the b39 poses."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import (B39GetupEnv, FALLEN_POSES,
                                       roll_pitch_to_quat)
from training.b_line.getup_executor import GetupExecutor, pose_from_attitude

POSES = ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg")
VARIANTS_DEG = {
    "roll_pos": [(0.0, 0.0), (-10.0, 0.0), (10.0, 0.0)],
    "roll_neg": [(0.0, 0.0), (-10.0, 0.0), (10.0, 0.0)],
    "pitch_pos": [(0.0, 0.0), (-20.0, -20.0), (-20.0, 0.0), (-20.0, 20.0),
                  (-10.0, -10.0), (-10.0, 10.0), (0.0, -20.0), (0.0, 20.0),
                  (10.0, -10.0), (10.0, 10.0), (20.0, -20.0), (20.0, 0.0),
                  (20.0, 20.0)],
    "pitch_neg": [(0.0, 0.0), (-10.0, 0.0), (10.0, 0.0)],
}


def reset_variant(env, pose, roll_off_deg, pitch_off_deg):
    base_roll, base_pitch = FALLEN_POSES[pose]
    env.data.qpos[:] = 0.0
    env.data.qvel[:] = 0.0
    env.data.qpos[0:3] = [0.0, 0.0, 0.08]
    env.data.qpos[3:7] = roll_pitch_to_quat(
        base_roll + math.radians(roll_off_deg),
        base_pitch + math.radians(pitch_off_deg))
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
    env.current_pose_name = pose
    return env._obs(), {"pose": pose}


def run(env, pose, executor, max_steps=700):
    obs = env._obs()
    info = {}
    for _ in range(max_steps):
        action = executor.action(env, obs)
        obs, _, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    return bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50, info


def main():
    rows = []
    for pose in POSES:
        for droll, dpitch in VARIANTS_DEG[pose]:
            env = B39GetupEnv(fallen_poses=(pose,))
            reset_variant(env, pose, droll, dpitch)
            executor = GetupExecutor(pose)
            ok, info = run(env, pose, executor)
            pen = float(info.get("pen", 0.0))
            print(f"{pose:10s} d=({droll:+.0f},{dpitch:+.0f}) ok={ok} "
                  f"up={info.get('upright', -9):+.2f} "
                  f"servo={np.round(info.get('servo_angles', []), 2).tolist()} "
                  f"pen={pen*1000:.1f}mm steps={env.step_count}", flush=True)
            rows.append((pose, droll, dpitch, ok))
            env.close()
    n = len(rows)
    ok_n = sum(r[3] for r in rows)
    print(f"\nEXECUTOR: {ok_n}/{n} ok")
    for r in rows:
        if not r[3]:
            print(" FAIL", r)


if __name__ == "__main__":
    main()
