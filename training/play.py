#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load a trained policy and run it in the MuJoCo viewer.

Example:
    python training/play.py --model models/sr_ppo.zip --episodes 3
"""

from __future__ import annotations

import argparse
import time

from stable_baselines3 import PPO

from env_sr_2dof import Sr2DofEnv


def main():
    parser = argparse.ArgumentParser(description="Play a trained SR-Support policy")
    parser.add_argument("--model", required=True)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()

    env = Sr2DofEnv(render_mode=None if args.no_render else "human")
    model = PPO.load(args.model, device="cpu")

    for ep in range(args.episodes):
        obs, info = env.reset(seed=args.seed + ep)
        done = False
        total_reward = 0.0
        steps = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            steps += 1
            done = bool(terminated or truncated)
            if not args.no_render:
                env.render()
                time.sleep(1.0 / env.metadata["render_fps"])
        print(
            f"episode {ep + 1}: reward={total_reward:.1f} "
            f"steps={steps} tilt={info['tilt']:.2f} upright={info['upright']}"
        )

    env.close()


if __name__ == "__main__":
    main()
