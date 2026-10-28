"""Check rescue sequences from the fully-inverted stuck pose.

The push test (dir 0, mag 4 N at arm2) ends inverted at up_z=-0.88 with
q=[2.07, 0.8], and the policy never leaves it. Test scripted rescues from that
pose:
  A. RT_ROLL: shoulder 1.6, elbow 0.9, hold, creep to zero.
  B. Home directly: both targets to zero.
  C. Inverted pump: shoulder at +2.07, elbow full square wave.
  D. Inverted pump: shoulder at -1.07, elbow full square wave (current pump).
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


class NoHomer:
    state = "policy"

    def apply(self, env):
        return False

    def update(self, env, info):
        pass


def run_policy(model, env, obs, steps):
    info = None
    for _ in range(steps):
        a, _ = model.predict(obs, deterministic=True)
        obs, _, _, _, info = env.step(a)
    return obs, info


def drive(env, target, max_ticks=200, rate=0.08):
    """Ramp ctrl target to target at fixed rate; returns ticks used."""
    base = env.unwrapped
    for t in range(max_ticks):
        cur = base._prev_cmd.copy()
        base.ctrl_override = cur + np.clip(np.asarray(target) - cur, -rate, rate)
        _, _, _, _, info = env.step(np.zeros(2))
        if np.max(np.abs(np.asarray(target) - base._prev_cmd)) < 1e-2:
            return t + 1, info
    return max_ticks, info


def hold(env, target, ticks):
    env.unwrapped.ctrl_override = np.asarray(target, dtype=float).copy()
    info = None
    for _ in range(ticks):
        _, _, _, _, info = env.step(np.zeros(2))
    return info


def rescue_roll(env):
    drive(env, [1.6, 0.9], 120)
    hold(env, [1.6, 0.9], 50)
    # creep to zero
    base = env.unwrapped
    for _ in range(400):
        cur = base._prev_cmd.copy()
        base.ctrl_override = cur + np.clip(-cur, -0.02, 0.02)
        _, _, _, _, info = env.step(np.zeros(2))
        if np.max(np.abs(base._prev_cmd)) < 0.03:
            base.ctrl_override = np.zeros(2)
            _, _, _, _, info = env.step(np.zeros(2))
            break
    return info


def rescue_home(env):
    return drive(env, [0.0, 0.0], 300)[1]


def rescue_pump(env, shoulder):
    base = env.unwrapped
    base.ctrl_override = np.array([shoulder, base._prev_cmd[1]])
    env.step(np.zeros(2))
    info = None
    for t in range(400):
        goal = 1.55 if (t // 40) % 2 == 0 else -1.55
        cur = base._prev_cmd.copy()
        cmd = cur.copy()
        cmd[0] = shoulder
        cmd[1] += float(np.clip(goal - cmd[1], -0.08, 0.08))
        base.ctrl_override = cmd
        _, _, _, _, info = env.step(np.zeros(2))
        if float(info["up_z"]) > 0.9:
            break
    return info


def make_stuck(model, seed):
    env = HomerWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                    random_init=True, seed=9))
    obs, _ = env.reset(seed=seed, options={"quat": [1, 0, 0, 0], "arm_q": [0.0, 0.0]})
    d = env.unwrapped.data
    for _ in range(20):
        d.xfrc_applied[3] = (4.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        obs, _, _, _, info = env.step(np.zeros(2))
        if float(info["up_z"]) < 0.7:
            break
    d.xfrc_applied[3] = 0.0
    obs, info = run_policy(model, env, obs, 1200)
    return env, info


def main():
    model = PPO.load(str(MODEL), device="cpu")
    for name, fn in (("roll", rescue_roll), ("home", rescue_home),
                     ("pump_+2.07", lambda e: rescue_pump(e, 2.07)),
                     ("pump_-1.07", lambda e: rescue_pump(e, -1.07))):
        env, info = make_stuck(model, seed=500)
        env.homer = NoHomer()
        print(f"--- {name}: stuck up={float(info['up_z']):+.2f} "
              f"q={np.round(env.unwrapped._prev_cmd, 2)}")
        info = fn(env)
        print(f"    after rescue: up={float(info['up_z']):+.2f} "
              f"q={np.round(env.unwrapped._prev_cmd, 2)} "
              f"homer={env.homer.state}")
        env.close()


if __name__ == "__main__":
    main()
