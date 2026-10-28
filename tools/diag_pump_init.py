"""Sweep pump-start conditions matching the hardware stall poses.

The hardware pump starts with the shoulder already at its short-side limit and
the elbow wherever the policy parked it (policy elbow cap +-0.8). The pump
square wave has a 20-tick half period and 0.08 rad/tick slew, so it can only
travel 1.6 rad per half period -- less than the 3.1 rad full elbow range. This
sweep checks whether the starting elbow angle changes the pump outcome.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.selfright_env import SelfRightEnv, _quat_mul, _roll_pitch_quat, _yaw_quat
from training.b_line.stand_homer import HomerWrapper

MODEL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
ROBOT = "b39rq_sr5"
CAP = 2200


def main():
    model = PPO.load(str(MODEL), device="cpu")
    up_z_targets = (0.2, 0.45, 0.65)
    elbow_inits = (-0.8, 0.0, 0.8)
    n_ok = 0
    n_all = 0
    fails = []
    for upz in up_z_targets:
        theta = math.acos(upz)
        for k in range(8):
            yaw = 2 * math.pi * k / 8
            quat = _quat_mul(_roll_pitch_quat(0.0, theta), _yaw_quat(yaw))
            for q2 in elbow_inits:
                env = HomerWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                                random_init=True, seed=11))
                obs, _ = env.reset(seed=300 + k,
                                   options={"quat": quat, "arm_q": [-1.07, q2],
                                            "z0": 0.12})
                states = set()
                pumped = False
                max_up = -1.0
                info = None
                for t in range(CAP):
                    a, _ = model.predict(obs, deterministic=True)
                    obs, _, _, _, info = env.step(a)
                    states.add(env.homer.state)
                    pumped = pumped or env.homer.state == "left_pump"
                    max_up = max(max_up, float(info["up_z"]))
                    if env.homer.state == "stand" and float(info["up_z"]) > 0.9:
                        break
                ok = info["up_z"] > 0.9 and float(np.max(np.abs(env.unwrapped._prev_cmd))) < 0.35
                n_all += 1
                n_ok += int(ok)
                if not ok:
                    fails.append((upz, k, q2, round(float(info["up_z"]), 2),
                                  round(max_up, 2), pumped,
                                  np.round(env.unwrapped._prev_cmd, 2).tolist(),
                                  sorted(states)))
                env.close()
        print(f"up_z={upz}: running {n_ok}/{n_all}", flush=True)
    print(f"\n{n_ok}/{n_all} ok")
    for f in fails:
        print("FAIL", f)


if __name__ == "__main__":
    main()
