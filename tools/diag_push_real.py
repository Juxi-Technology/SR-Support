"""Push-over test with the force applied to a real body (previous tests used
xfrc_applied[0], which is the world body and does nothing).

Pushes the tall arm (arm2 body) horizontally for 0.25 s, releasing early once
the body has tipped past up_z<0.7 (a hand push stops when it is falling).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.selfright_env import SelfRightEnv
from training.b_line.stand_homer import HomerWrapper

MODEL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
ROBOT = "b39rq_sr5"
CAP = 2500


def main():
    model = PPO.load(str(MODEL), device="cpu")
    ok_n = 0
    n = 0
    rows = []
    for k in range(8):
        ang = 2 * math.pi * k / 8
        for mag in (0.5, 1.0, 2.0, 4.0):
            env = HomerWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                            random_init=True, seed=9))
            obs, _ = env.reset(seed=500 + k,
                               options={"quat": [1, 0, 0, 0], "arm_q": [0.0, 0.0]})
            d = env.unwrapped.data
            m = env.unwrapped.model
            arm2 = 3  # body id in this model
            fx, fy = mag * math.cos(ang), mag * math.sin(ang)
            min_up = 1.0
            pushed_ticks = 0
            for t in range(20):  # up to 0.4 s, release once tipping
                d.xfrc_applied[arm2] = (fx, fy, 0.0, 0.0, 0.0, 0.0)
                obs, _, _, _, info = env.step(np.zeros(2))
                min_up = min(min_up, float(info["up_z"]))
                pushed_ticks += 1
                if float(info["up_z"]) < 0.7:
                    break
            d.xfrc_applied[arm2] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            states = set()
            max_up = -1.0
            for t in range(CAP):
                a, _ = model.predict(obs, deterministic=True)
                obs, _, _, _, info = env.step(a)
                states.add(env.homer.state)
                max_up = max(max_up, float(info["up_z"]))
                if env.homer.state == "stand" and float(info["up_z"]) > 0.9:
                    break
            ok = info["up_z"] > 0.9 and float(np.max(np.abs(env.unwrapped._prev_cmd))) < 0.35
            ok_n += int(ok)
            n += 1
            rows.append((k, mag, ok, round(min_up, 2), round(float(info["up_z"]), 2),
                         round(max_up, 2), pushed_ticks, sorted(states)))
            env.close()
        print(f"dir {k}/8 done: {ok_n}/{n} ok", flush=True)
    print(f"\n{ok_n}/{n} ok")
    for r in rows:
        if not r[2]:
            print("FAIL", r)


if __name__ == "__main__":
    main()
