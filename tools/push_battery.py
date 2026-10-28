"""Systematic self-righting battery for the b39 build (policy + PushStand).

Part A: random fallen orientations (uniform quats), policy + routine runs.
Part B: standing robot pushed with a horizontal impulse from 8 directions,
        two magnitudes, to mimic hand pushes in the viewer.

Writes logs/push_battery.json and prints a summary.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import mujoco
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.selfright_env import SelfRightEnv
from training.b_line.stand_homer import HomerWrapper

OUT = ROOT / "logs" / "push_battery.json"
MODEL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
ROBOT = "b39rq_sr5"
CAP = 2000
PEN_TOL = 0.005   # max arm-floor/base penetration allowed for a valid stand


def up_body(env):
    return np.round(env.unwrapped._up_body(), 2).tolist()


def evaluate(env, info, pen_min: float = 0.0) -> dict:
    ok = (info["up_z"] > 0.9
          and float(np.max(np.abs(env.unwrapped._prev_cmd))) < 0.35
          and pen_min > -PEN_TOL)
    return {
        "ok": bool(ok),
        "up_z": round(float(info["up_z"]), 2),
        "q": [round(float(x), 2) for x in env.unwrapped._prev_cmd],
        "state": env.homer.state,
        "pen_min_mm": round(pen_min * 1000.0, 1),
    }


def run_random(model, n=40):
    rng = np.random.default_rng(1000)
    rows = []
    for i in range(n):
        env = HomerWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                        random_init=True, seed=3), fall_gate=True)
        obs, _ = env.reset(seed=int(rng.integers(1 << 30)))
        start = up_body(env)
        pen_min = 0.0
        for t in range(CAP):
            a, _ = model.predict(obs, deterministic=True)
            obs, _, te, tr, info = env.step(a)
            pen_min = min(pen_min, env.unwrapped.arm_penetration())
            if env.homer.state == "stand":
                break
        r = {"kind": "random", "i": i, "start_up": start, **evaluate(env, info, pen_min)}
        env.close()
        rows.append(r)
        print(f"random {i}: start={start} -> ok={r['ok']} up_z={r['up_z']} "
              f"pen={r['pen_min_mm']}mm st={r['state']}")
    return rows


def run_pushes(model, directions=8, magnitudes=(1.0, 2.0)):
    rows = []
    for k in range(directions):
        ang = 2 * math.pi * k / directions
        for mag in magnitudes:
            env = HomerWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                            random_init=True, seed=3), fall_gate=True)
            obs, _ = env.reset(seed=100, options={"quat": [1, 0, 0, 0], "arm_q": [0.0, 0.0]})
            d = env.unwrapped.data
            arm2 = mujoco.mj_name2id(env.unwrapped.model,
                                     mujoco.mjtObj.mjOBJ_BODY, "arm2")
            pen_min = 0.0
            fx, fy = mag * math.cos(ang), mag * math.sin(ang)
            for t in range(10):  # 0.2 s push on the tall arm
                d.xfrc_applied[arm2] = (fx, fy, 0.0, 0.0, 0.0, 0.0)
                obs, _, te, tr, info = env.step(np.zeros(2))
                pen_min = min(pen_min, env.unwrapped.arm_penetration())
            d.xfrc_applied[arm2] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            for t in range(CAP):
                a, _ = model.predict(obs, deterministic=True)
                obs, _, te, tr, info = env.step(a)
                pen_min = min(pen_min, env.unwrapped.arm_penetration())
                if env.homer.state == "stand":
                    break
            r = {"kind": "push", "dir_deg": round(math.degrees(ang)), "mag": mag,
                 **evaluate(env, info, pen_min)}
            env.close()
            rows.append(r)
            print(f"push dir={r['dir_deg']} mag={mag}: ok={r['ok']} up_z={r['up_z']} "
                  f"pen={r['pen_min_mm']}mm st={r['state']}")
    return rows


def main() -> None:
    model = PPO.load(str(MODEL), device="cpu")
    rows = run_random(model) + run_pushes(model)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    fails = [r for r in rows if not r["ok"]]
    print(f"\n{len(rows) - len(fails)}/{len(rows)} ok; failures:")
    for r in fails:
        print(" ", r)


if __name__ == "__main__":
    main()
