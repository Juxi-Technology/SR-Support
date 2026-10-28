"""Validate the two-policy controller on the 56-case battery."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import mujoco
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.selfright_env import SelfRightEnv
from training.b_line.stand_homer import FallGate
from training.b_line.two_policy import TwoPolicy

FALL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
STAND = ROOT / "training/b_line/models/ppo_b39_ap_ft/best/best_model.zip"
CAP = 2000


def run(env, obs, gate, two, push=None):
    d = env.data
    if push is not None:
        fx, fy = push
        for _ in range(10):
            d.xfrc_applied[3] = (fx, fy, 0, 0, 0, 0)
            obs, _, _, _, info = env.step(np.zeros(2))
            gate.update(env, info)
        d.xfrc_applied[3] = 0
    pen = 0.0
    for t in range(CAP):
        action = two.act(obs, env) if gate.armed else np.zeros(2)
        obs, _, _, _, info = env.step(action)
        gate.update(env, info)
        pen = min(pen, env.arm_penetration())
        if info["up_z"] > 0.9 and np.max(np.abs(env._prev_cmd)) < 0.35:
            hold = 0
            for _ in range(25):
                action = two.act(obs, env) if gate.armed else np.zeros(2)
                obs, _, _, _, info = env.step(action)
                gate.update(env, info)
                pen = min(pen, env.arm_penetration())
                if info["up_z"] > 0.9 and np.max(np.abs(env._prev_cmd)) < 0.35:
                    hold += 1
                else:
                    break
            if hold >= 25:
                break
    return info, pen


def main():
    fall = PPO.load(str(FALL), device="cpu")
    stand = PPO.load(str(STAND), device="cpu")
    rng = np.random.default_rng(1000)
    rows = []
    for i in range(40):
        env = SelfRightEnv(robot="b39rq_sr5", domain_randomization=False,
                           random_init=True, seed=3)
        obs, _ = env.reset(seed=int(rng.integers(1 << 30)))
        gate = FallGate(); two = TwoPolicy(fall, stand)
        info, pen = run(env, obs, gate, two)
        ok = (info["up_z"] > 0.9 and np.max(np.abs(env._prev_cmd)) < 0.35
              and pen > -0.005)
        rows.append(ok)
        print(f"random {i}: ok={ok} up={info['up_z']:+.2f} "
              f"q={np.round(env._prev_cmd,2)} pen={pen*1000:.1f}mm", flush=True)
        env.close()
    for k in range(8):
        ang = 2 * math.pi * k / 8
        for mag in (1.0, 2.0):
            env = SelfRightEnv(robot="b39rq_sr5", domain_randomization=False,
                               random_init=True, seed=3)
            obs, _ = env.reset(seed=100, options={"quat": [1, 0, 0, 0],
                                                  "arm_q": [0.0, 0.0]})
            gate = FallGate(); two = TwoPolicy(fall, stand)
            fx, fy = mag * math.cos(ang), mag * math.sin(ang)
            info, pen = run(env, obs, gate, two, push=(fx, fy))
            ok = (info["up_z"] > 0.9 and np.max(np.abs(env._prev_cmd)) < 0.35
                  and pen > -0.005)
            rows.append(ok)
            print(f"push dir={math.degrees(ang):.0f} mag={mag}: ok={ok} "
                  f"up={info['up_z']:+.2f} q={np.round(env._prev_cmd,2)} "
                  f"pen={pen*1000:.1f}mm", flush=True)
            env.close()
    print(f"TWO POLICY: {sum(rows)}/{len(rows)} ok")


if __name__ == "__main__":
    main()
