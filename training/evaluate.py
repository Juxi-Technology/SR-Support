#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate a trained policy over N episodes and report success rate.

Success = episode ended with `terminated=True` (upright for 0.5 s), not timeout.
This is a simulation-only check; it does not replace real-hardware testing.

Example:
    python training/evaluate.py --model models/sr_ppo.zip --episodes 100
"""

from __future__ import annotations

import argparse

from stable_baselines3 import PPO

from env_sr_2dof import Sr2DofEnv


def main():
    parser = argparse.ArgumentParser(description="Evaluate SR-Support policy")
    parser.add_argument("--model", required=True)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    env = Sr2DofEnv(render_mode=None)
    model = PPO.load(args.model, device="cpu")

    successes = 0
    for ep in range(args.episodes):
        obs, info = env.reset(seed=args.seed + ep)
        done = False
        steps = 0
        terminated = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            done = bool(terminated or truncated)
        successes += int(terminated)
        if (ep + 1) % 10 == 0 or args.episodes <= 10:
            print(
                f"episode {ep + 1}/{args.episodes}: "
                f"success={int(terminated)} steps={steps} "
                f"tilt={info['tilt']:.2f}"
            )

    print(
        f"success {successes}/{args.episodes} "
        f"({100.0 * successes / max(1, args.episodes):.1f}%)"
    )
    env.close()


if __name__ == "__main__":
    main()
