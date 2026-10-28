"""Diagnose self-righting on harder cases than push_battery.py.

Part A: standing robot pushed with strong horizontal impulses.
Part B: starts from orientations in the inverted hemisphere (up_z < -0.3).

Same policy + PushStand as deployment. Prints one line per case.
"""

from __future__ import annotations

import math
import sys

import mujoco
import numpy as np
from stable_baselines3 import PPO

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from training.b_line.selfright_env import SelfRightEnv, _random_quat
from training.b_line.stand_homer import HomerWrapper

MODEL = "training/b_line/models/ppo_b39_rq/final.zip"
ROBOT = "b39rq_sr5"
CAP = 2000


def make_env():
    return HomerWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                     random_init=True, seed=7))


def run(model, env, obs, label, push=None):
    if push is not None:
        fx, fy = push
        arm2 = mujoco.mj_name2id(env.unwrapped.model,
                                 mujoco.mjtObj.mjOBJ_BODY, "arm2")
        for _ in range(15):
            env.unwrapped.data.xfrc_applied[arm2] = (fx, fy, 0.0, 0.0, 0.0, 0.0)
            obs, _, _, _, info = env.step(np.zeros(2))
        env.unwrapped.data.xfrc_applied[arm2] = 0.0
    max_up = -1.0
    states = set()
    for _ in range(CAP):
        a, _ = model.predict(obs, deterministic=True)
        obs, _, te, tr, info = env.step(a)
        max_up = max(max_up, float(info["up_z"]))
        states.add(env.homer.state)
        if env.homer.state == "stand" and float(info["up_z"]) > 0.9:
            break
    ok = info["up_z"] > 0.9 and float(np.max(np.abs(env.unwrapped._prev_cmd))) < 0.35
    print(f"{label}: ok={ok} up_z={info['up_z']:+.2f} max_up={max_up:+.2f} "
          f"q={np.round(env.unwrapped._prev_cmd, 2).tolist()} "
          f"states={sorted(states)}", flush=True)
    env.close()
    return ok


def main():
    model = PPO.load(MODEL, device="cpu")
    print("--- strong pushes from standing ---")
    oks = []
    for k in range(8):
        ang = 2 * math.pi * k / 8
        for mag in (3.0, 6.0, 10.0):
            env = make_env()
            obs, _ = env.reset(seed=200 + k,
                               options={"quat": [1, 0, 0, 0], "arm_q": [0.0, 0.0]})
            ok = run(model, env, obs, f"push dir={math.degrees(ang):3.0f} mag={mag:4.1f}",
                     push=(mag * math.cos(ang), mag * math.sin(ang)))
            oks.append(ok)
    print(f"pushes {sum(oks)}/{len(oks)}")

    print("--- inverted starts (up_z < -0.3) ---")
    rng = np.random.default_rng(4242)
    oks2 = []
    n = 0
    while n < 20:
        quat = _random_quat(rng)
        # body up in world = R.T e_z; for a quaternion (w,x,y,z),
        # up_z = 1 - 2(x^2 + y^2)
        up_z = 1.0 - 2.0 * (quat[1] ** 2 + quat[2] ** 2)
        if up_z > -0.3:
            continue
        env = make_env()
        obs, _ = env.reset(seed=int(rng.integers(1 << 30)),
                           options={"quat": quat, "arm_q": [0.0, 0.0], "z0": 0.15})
        ok = run(model, env, obs, f"inv {n} init_up_z={up_z:+.2f}")
        oks2.append(ok)
        n += 1
    print(f"inverted {sum(oks2)}/{len(oks2)}")


if __name__ == "__main__":
    main()
