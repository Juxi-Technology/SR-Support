#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Train PPO on the independent SR-Support 2-DOF environment.

Example:
    python training/train_ppo.py --timesteps 2000000 --n-envs 4

This script uses Stable-Baselines3 (MIT) and MuJoCo (Apache-2.0). The
environment/model are our own; no SelfRisingRobot code or weights are used.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecMonitor

from env_sr_2dof import Sr2DofEnv


def build_model(env, args):
    return PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=args.n_steps,
        batch_size=256,
        n_epochs=10,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.005,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=dict(
            net_arch=[64, 64],
            activation_fn=torch.nn.Tanh,
            squash_output=True,
        ),
        seed=args.seed,
        device="auto",
    )


def main():
    parser = argparse.ArgumentParser(description="Train PPO for SR-Support 2-DOF")
    parser.add_argument("--timesteps", type=int, default=2_000_000)
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument("--n-steps", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="models/sr_ppo", help="model output prefix")
    args = parser.parse_args()

    def make_env():
        return Sr2DofEnv(randomize=True)

    env = make_vec_env(make_env, n_envs=args.n_envs, seed=args.seed)
    env = VecMonitor(env)

    model = build_model(env, args)
    model.learn(total_timesteps=args.timesteps, progress_bar=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    print(f"Saved model to {out}.zip")

    env.close()


if __name__ == "__main__":
    main()
