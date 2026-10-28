"""Compare the elbow pump at 20-tick vs 40-tick half periods.

20 ticks * 0.08 rad = 1.6 rad, half of the elbow's 3.1 rad travel: the pump
never reaches the opposite limit, and its actual range depends on the elbow
angle when the pump starts. 40 ticks covers the full range.
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
from training.b_line.stand_homer import HomerWrapper, PushStand

MODEL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
ROBOT = "b39rq_sr5"
CAP = 2200


class PeriodWrapper(HomerWrapper):
    def __init__(self, env, period):
        self._period = period
        super().__init__(env)

    def _make(self):
        return PushStand(pump_period=self._period)


def sweep(model, period, up_z_targets=(0.2, 0.45, 0.65), elbow_inits=(0.8,), dirs=8):
    ok_n = 0
    n = 0
    worst = []
    for upz in up_z_targets:
        theta = math.acos(upz)
        for k in range(dirs):
            yaw = 2 * math.pi * k / dirs
            quat = _quat_mul(_roll_pitch_quat(0.0, theta), _yaw_quat(yaw))
            for q2 in elbow_inits:
                env = PeriodWrapper(SelfRightEnv(robot=ROBOT, domain_randomization=False,
                                                 random_init=True, seed=11), period)
                obs, _ = env.reset(seed=300 + k,
                                   options={"quat": quat, "arm_q": [-1.07, q2],
                                            "z0": 0.12})
                info = None
                q2_cmds = []
                pumped = False
                for t in range(CAP):
                    a, _ = model.predict(obs, deterministic=True)
                    obs, _, _, _, info = env.step(a)
                    if env.homer.state == "left_pump":
                        pumped = True
                        q2_cmds.append(float(env.unwrapped._prev_cmd[1]))
                    if env.homer.state == "stand" and float(info["up_z"]) > 0.9:
                        break
                ok = info["up_z"] > 0.9 and float(np.max(np.abs(env.unwrapped._prev_cmd))) < 0.35
                ok_n += int(ok)
                n += 1
                rng = (round(min(q2_cmds), 2), round(max(q2_cmds), 2)) if q2_cmds else None
                if not ok:
                    worst.append((upz, k, q2, round(float(info["up_z"]), 2), pumped, rng))
                env.close()
    return ok_n, n, worst


def main():
    model = PPO.load(str(MODEL), device="cpu")
    for period in (20, 40, 45):
        ok_n, n, worst = sweep(model, period)
        print(f"period={period}: {ok_n}/{n} ok; fails={worst}", flush=True)


if __name__ == "__main__":
    main()
