"""Same corrected push test, but with a chosen b39 XML variant.

Used to check whether enabling self-collision (the b39 asset change) created
the fully-inverted stuck poses.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line import selfright_env as se
from training.b_line.selfright_env import SelfRightEnv
from training.b_line.stand_homer import HomerWrapper

MODEL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
CAP = 2500


def main():
    xml = sys.argv[1] if len(sys.argv) > 1 else "assets/robot_selfrising_b39_h26_ri.xml"
    tag = sys.argv[2] if len(sys.argv) > 2 else "variant"
    se.ROBOT_SPECS["b39_variant"] = dict(se.ROBOT_SPECS["b39rq_sr5"], xml=xml)
    model = PPO.load(str(MODEL), device="cpu")
    ok_n = 0
    n = 0
    fails = []
    for k in range(8):
        ang = 2 * math.pi * k / 8
        for mag in (0.5, 1.0, 2.0, 4.0):
            env = HomerWrapper(SelfRightEnv(robot="b39_variant", domain_randomization=False,
                                            random_init=True, seed=9))
            obs, _ = env.reset(seed=500 + k,
                               options={"quat": [1, 0, 0, 0], "arm_q": [0.0, 0.0]})
            d = env.unwrapped.data
            fx, fy = mag * math.cos(ang), mag * math.sin(ang)
            for _ in range(20):
                d.xfrc_applied[3] = (fx, fy, 0.0, 0.0, 0.0, 0.0)
                obs, _, _, _, info = env.step(np.zeros(2))
                if float(info["up_z"]) < 0.7:
                    break
            d.xfrc_applied[3] = 0.0
            for _ in range(CAP):
                a, _ = model.predict(obs, deterministic=True)
                obs, _, _, _, info = env.step(a)
                if env.homer.state == "stand" and float(info["up_z"]) > 0.9:
                    break
            ok = info["up_z"] > 0.9 and float(np.max(np.abs(env.unwrapped._prev_cmd))) < 0.35
            ok_n += int(ok)
            n += 1
            if not ok:
                fails.append((k, mag, round(float(info["up_z"]), 2),
                              np.round(env.unwrapped._prev_cmd, 2).tolist()))
            env.close()
        print(f"{tag} dir {k}/8: {ok_n}/{n}", flush=True)
    print(f"{tag}: {ok_n}/{n} ok; fails={fails}")


if __name__ == "__main__":
    main()
