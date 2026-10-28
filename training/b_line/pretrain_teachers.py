"""Distill several face specialists into one policy, then PPO fine-tune.

Teachers are selected per canonical fallen pose. Only successful rollouts are
used. The student is behavior-cloned from the combined successful transitions
and then trained on all four poses.

This is based on Juxi-Technology/2dof-selfrighting-robot sim/pretrain_teachers.py
(MIT/Apache-2.0); see third_party/juxi-2dof/.

Run (from the repository root):
  python -m training.b_line.pretrain_teachers --robot selfrising \
    --teachers roll_pos=training/b_line/models/ppo_selfrising_roll_pos/final.zip,roll_neg=... \
    --hidden 128 --steps 2000000

Teacher models must be trained first, e.g.:
  python -m training.b_line.train --robot selfrising --poses roll_pos \
    --run-name ppo_selfrising_roll_pos --hidden 128 --steps 2000000
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

from .selfright_env import POSE_RP, SelfRightEnv, make_env

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"


def collect_teacher(
    env: SelfRightEnv,
    model: PPO,
    pose: str,
    episodes: int,
    seed: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    samples: list[tuple[np.ndarray, np.ndarray]] = []
    for ep in range(episodes):
        options = {
            "pose": pose,
            "yaw": 0.0 if ep == 0 else float(rng.uniform(-np.pi, np.pi)),
            "arm_q": [0.0, 0.0] if ep == 0 else rng.uniform(-0.10, 0.10, 2).tolist(),
        }
        obs, _ = env.reset(seed=seed + ep, options=options)
        trajectory: list[tuple[np.ndarray, np.ndarray]] = []
        uprights: list[bool] = []
        for _ in range(env.episode_steps):
            action, _ = model.predict(obs, deterministic=True)
            trajectory.append((np.asarray(obs, dtype=np.float32), np.asarray(action, dtype=np.float32)))
            obs, _, terminated, truncated, info = env.step(action)
            uprights.append(bool(info["upright"]))
            if terminated or truncated:
                break
        if np.mean(uprights[-25:]) >= 0.9:
            samples.extend(trajectory)
    return samples


def behavior_clone(model: PPO, obs: np.ndarray, act: np.ndarray, epochs: int, batch: int) -> None:
    policy = model.policy
    params = list(policy.mlp_extractor.policy_net.parameters()) + list(policy.action_net.parameters())
    opt = torch.optim.Adam(params, lr=1e-3)
    obs_t = torch.as_tensor(obs, dtype=torch.float32)
    act_t = torch.as_tensor(act, dtype=torch.float32)
    n = len(obs_t)
    for epoch in range(epochs):
        perm = torch.randperm(n)
        total = 0.0
        batches = 0
        for start in range(0, n, batch):
            idx = perm[start : start + batch]
            features = policy.extract_features(obs_t[idx])
            latent_pi, _ = policy.mlp_extractor(features)
            pred = policy.action_net(latent_pi)
            loss = torch.mean((pred - act_t[idx]) ** 2)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.item())
            batches += 1
        if epoch % 20 == 0 or epoch == epochs - 1:
            print(f"  bc epoch {epoch:03d} mse={total / max(batches, 1):.5f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--robot", default="selfrising")
    ap.add_argument(
        "--teachers",
        required=True,
        help="comma-separated pose=model.zip pairs",
    )
    ap.add_argument("--episodes-per-teacher", type=int, default=30)
    ap.add_argument("--steps", type=int, default=2_000_000)
    ap.add_argument("--n-envs", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bc-epochs", type=int, default=300)
    ap.add_argument("--bc-batch", type=int, default=256)
    ap.add_argument("--hidden", type=int, default=128)
    ap.add_argument("--run-name", default="ppo_selfrising_distill")
    args = ap.parse_args()

    teachers = {}
    for item in args.teachers.split(","):
        pose, path = item.split("=", 1)
        pose = pose.strip()
        path = path.strip()
        assert pose in POSE_RP, f"unknown pose {pose}"
        teachers[pose] = PPO.load(path, device="cpu")
        print(f"teacher {pose}: {path}")

    torch.set_num_threads(4)
    torch.manual_seed(args.seed)
    env = SelfRightEnv(
        robot=args.robot, domain_randomization=False, random_init=False, seed=args.seed
    )
    obs_all: list[np.ndarray] = []
    act_all: list[np.ndarray] = []
    for i, (pose, model) in enumerate(teachers.items()):
        samples = collect_teacher(env, model, pose, args.episodes_per_teacher, args.seed + 1000 * i)
        print(f"  {pose}: {len(samples)} successful transitions")
        for obs, act in samples:
            obs_all.append(obs)
            act_all.append(act)
    env.close()
    if not obs_all:
        raise SystemExit("no successful teacher trajectories; nothing to distill")
    obs = np.stack(obs_all)
    act = np.stack(act_all)
    print(f"dataset: {obs.shape[0]} samples")

    run_dir = MODELS / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    vec_env = DummyVecEnv(
        [make_env(i, args.seed, robot=args.robot) for i in range(args.n_envs)]
    )
    vec_env = VecMonitor(vec_env)
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
        verbose=0,
    )
    behavior_clone(model, obs, act, args.bc_epochs, args.bc_batch)
    model.save(run_dir / "bc")
    print(f"saved {run_dir / 'bc.zip'}")
    model.learn(total_timesteps=args.steps, progress_bar=False)
    model.save(run_dir / "final")
    print(f"saved {run_dir / 'final.zip'}")
    vec_env.close()


if __name__ == "__main__":
    main()
