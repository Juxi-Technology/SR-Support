"""PPO fine-tune of the b39 get-up policy after BC pretraining.

Mirrors the original SelfRisingRobot train_robo1.py: continue the PPO model
from the behavior-cloned policy, 6 parallel environments, 200k steps.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import SubprocVecEnv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv

BC = ROOT / "training/b_line/models/getup_b39_bc/final.zip"
OUT = ROOT / "training/b_line/models/getup_b39_ppo"


def make_env(seed):
    def _init():
        env = B39GetupEnv()
        env.reset(seed=seed)
        return env
    return _init


def evaluate(model):
    for pose in ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg"):
        env = B39GetupEnv(fallen_poses=(pose,))
        obs, _ = env.reset(options={"pose": pose})
        best_up = -1.0
        final = {}
        for _ in range(env.max_steps):
            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, info = env.step(action)
            best_up = max(best_up, float(info["upright"]))
            final = info
            if terminated or truncated:
                break
        print(pose, "best_up", round(best_up, 3),
              "goal", bool(final.get("goal_pose")),
              "servo", np.round(final.get("servo_angles", []), 2).tolist(),
              "pen_mm", round(float(final.get("pen", 0.0)) * 1000, 1), flush=True)
        env.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=200_000)
    p.add_argument("--n-envs", type=int, default=6)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--ent", type=float, default=0.005)
    args = p.parse_args()
    env = SubprocVecEnv([make_env(args.seed + i) for i in range(args.n_envs)])
    model = PPO.load(str(BC), env=env, device="cpu")
    model.verbose = 1
    model.ent_coef = args.ent
    model.lr_schedule = lambda _: args.lr
    OUT.mkdir(parents=True, exist_ok=True)
    eval_env = B39GetupEnv()
    callback = EvalCallback(
        eval_env,
        best_model_save_path=str(OUT / "best"),
        log_path=str(OUT / "eval"),
        eval_freq=20_000,
        n_eval_episodes=8,
        deterministic=True,
        verbose=1,
    )
    model.learn(total_timesteps=args.steps, callback=callback)
    OUT.mkdir(parents=True, exist_ok=True)
    model.save(str(OUT / "final"))
    print("saved", OUT / "final.zip", flush=True)
    print("--- final ---", flush=True)
    evaluate(model)
    best_path = OUT / "best" / "best_model.zip"
    if best_path.exists():
        print("--- best ---", flush=True)
        evaluate(PPO.load(str(best_path), device="cpu"))
    env.close()


if __name__ == "__main__":
    main()
