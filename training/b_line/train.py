"""Train PPO on the SR-Support self-righting robot (2x PTK7452MG).

Examples (from the repository root):
  python -m training.b_line.train --robot selfrising --steps 3_000_000 --n-envs 8
  python -m training.b_line.train --robot selfrising --poses roll_pos --run-name ppo_selfrising_roll_pos

This is based on Juxi-Technology/2dof-selfrighting-robot sim/train.py
(MIT/Apache-2.0); see third_party/juxi-2dof/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

from .selfright_env import ROBOT_SPECS, SelfRightEnv, make_env

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=3_000_000)
    p.add_argument("--n-envs", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--robot", choices=sorted(ROBOT_SPECS), default="selfrising_sr5")
    p.add_argument("--run-name", type=str, default=None)
    p.add_argument("--hidden", type=int, default=128, help="MLP hidden width (B-line used 128)")
    p.add_argument("--smoke", action="store_true", help="short run without eval callback")
    p.add_argument("--init", type=str, default=None,
                   help="continue PPO training from this model zip (e.g. a get-up policy)")
    p.add_argument("--poses", type=str, default=None, help="comma-separated POSE_RP keys to train on")
    p.add_argument("--homer", action="store_true",
                   help="let the firmware-style stand homer finish the stand in training")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.smoke:
        args.steps = min(args.steps, 40_000)
        args.n_envs = min(args.n_envs, 4)

    torch.set_num_threads(4)
    run_name = args.run_name or f"ppo_{args.robot}"
    run_dir = MODELS / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    poses = [p.strip() for p in args.poses.split(",")] if args.poses else None
    # DummyVecEnv is slower than SubprocVecEnv but works on Windows without
    # pickling nested env factories. Reduce --n-envs if memory is tight.
    vec_env = DummyVecEnv(
        [make_env(i, args.seed, robot=args.robot, homer=args.homer, poses=poses)
         for i in range(args.n_envs)]
    )
    vec_env = VecMonitor(vec_env)

    if args.init:
        model = PPO.load(args.init, env=vec_env, device="cpu", print_system_info=False)
        print(f"continued from {args.init}")
    else:
        model = PPO(
            "MlpPolicy",
            vec_env,
            n_steps=1024,
            batch_size=2048,
            n_epochs=10,
            gamma=0.995,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.005,
            learning_rate=3e-4,
            vf_coef=0.5,
            max_grad_norm=1.0,
            policy_kwargs=dict(
                net_arch=dict(pi=[args.hidden, args.hidden], vf=[args.hidden, args.hidden]),
                activation_fn=torch.nn.Tanh,
            ),
            seed=args.seed,
            device="cpu",
            verbose=1,
        )

    callbacks = [
        CheckpointCallback(
            save_freq=max(50_000 // args.n_envs, 1),
            save_path=str(run_dir / "checkpoints"),
            name_prefix="ppo",
        )
    ]
    if not args.smoke:
        eval_env = SelfRightEnv(
            robot=args.robot, domain_randomization=False, random_init=True, seed=10_000
        )
        if args.homer:
            from .stand_homer import HomerWrapper

            eval_env = HomerWrapper(eval_env)
        callbacks.append(
            EvalCallback(
                eval_env,
                best_model_save_path=str(run_dir / "best"),
                log_path=str(run_dir / "eval"),
                eval_freq=max(50_000 // args.n_envs, 1),
                n_eval_episodes=20,
                deterministic=True,
                render=False,
            )
        )

    model.learn(total_timesteps=args.steps, callback=callbacks, progress_bar=False)
    model.save(str(run_dir / "final"))
    vec_env.close()
    print(f"saved {run_dir / 'final.zip'}")


if __name__ == "__main__":
    main()
