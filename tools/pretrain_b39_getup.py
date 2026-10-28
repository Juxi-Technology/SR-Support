"""Behavior-clone the searched b39 get-up references, then evaluate.

Mirrors the original SelfRisingRobot pretrain_robo1_from_scripted.py: the
reference waypoint sequences are rolled out from the four canonical poses
(plus small perturbations), and the PPO policy is supervised on the
(observation, action) pairs for 5000 epochs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import (B39GetupEnv, FALLEN_POSES,
                                       roll_pitch_to_quat)
from training.b_line.getup_reference_b39 import getup_sequence_for_pose

STEPS_PER_WP = 20
HOLD_STEPS = 10
OUT = ROOT / "training/b_line/models/getup_b39_bc"

POSE_VARIANTS_DEG = {
    "roll_pos": [(0.0, 0.0), (-10.0, 0.0), (10.0, 0.0)],
    "roll_neg": [(0.0, 0.0), (-10.0, 0.0), (10.0, 0.0)],
    "pitch_pos": [(0.0, 0.0), (-20.0, -20.0), (-20.0, 0.0), (-20.0, 20.0),
                  (-10.0, -10.0), (-10.0, 10.0), (0.0, -20.0), (0.0, 20.0),
                  (10.0, -10.0), (10.0, 10.0), (20.0, -20.0), (20.0, 0.0),
                  (20.0, 20.0)],
    "pitch_neg": [(0.0, 0.0), (-10.0, 0.0), (10.0, 0.0)],
}


def expert_target_schedule(sequence):
    out = []
    prev = np.zeros(2, dtype=np.float64)
    for wp in sequence:
        for i in range(STEPS_PER_WP):
            t = (i + 1) / STEPS_PER_WP
            out.append((1.0 - t) * prev + t * np.asarray(wp))
        prev = np.asarray(wp)
    out.extend([np.zeros(2)] * HOLD_STEPS)
    return out


def scripted_action(env, ctrl):
    return np.clip((np.asarray(ctrl) - env.target) / env.target_delta,
                   -1.0, 1.0).astype(np.float32)


def reset_variant(env, pose, roll_off_deg, pitch_off_deg):
    base_roll, base_pitch = FALLEN_POSES[pose]
    env.data.qpos[:] = 0.0
    env.data.qvel[:] = 0.0
    env.data.qpos[0:3] = [0.0, 0.0, 0.08]
    env.data.qpos[3:7] = roll_pitch_to_quat(
        base_roll + np.deg2rad(roll_off_deg),
        base_pitch + np.deg2rad(pitch_off_deg))
    env.target[:] = 0.0
    env.data.ctrl[:] = 0.0
    import mujoco
    mujoco.mj_forward(env.model, env.data)
    for _ in range(env.settle_steps):
        env.data.ctrl[:] = 0.0
        mujoco.mj_step(env.model, env.data)
    env.target[:] = 0.0
    env.data.ctrl[:] = 0.0
    env.step_count = 0
    env.success_count = 0
    env.prev_upright = env._upright()
    env.current_pose_name = pose
    return env._obs(), {"pose": pose}


def collect_expert_data():
    observations = []
    actions = []
    for pose in ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg"):
        sequence = getup_sequence_for_pose(pose)
        for roll_off, pitch_off in POSE_VARIANTS_DEG[pose]:
            env = B39GetupEnv(fallen_poses=(pose,))
            obs, _ = reset_variant(env, pose, roll_off, pitch_off)
            for ctrl in expert_target_schedule(sequence):
                action = scripted_action(env, ctrl)
                observations.append(obs.copy())
                actions.append(action.copy())
                obs, _, terminated, truncated, _ = env.step(action)
                if terminated or truncated:
                    break
            env.close()
    return (np.asarray(observations, dtype=np.float32),
            np.asarray(actions, dtype=np.float32))


def evaluate_policy(model):
    results = {}
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
        results[pose] = {"best_upright": round(best_up, 3),
                         "goal": bool(final.get("goal_pose")),
                         "servo": np.round(final.get("servo_angles", []), 2).tolist()}
        env.close()
    return results


def main():
    observations, actions = collect_expert_data()
    print("expert samples", len(observations))
    env = B39GetupEnv()
    model = PPO("MlpPolicy", env, n_steps=512, batch_size=256,
                learning_rate=3e-4, gamma=0.99, device="cpu")
    obs_t = torch.as_tensor(observations, dtype=torch.float32, device=model.device)
    act_t = torch.as_tensor(actions, dtype=torch.float32, device=model.device)
    optimizer = torch.optim.Adam(model.policy.parameters(), lr=1e-3)
    for epoch in range(5000):
        dist = model.policy.get_distribution(obs_t)
        pred = dist.distribution.mean
        loss = torch.mean((pred - act_t) ** 2)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if epoch % 500 == 0:
            print("epoch", epoch, "loss", float(loss.detach().cpu()), flush=True)
    results = evaluate_policy(model)
    for pose, result in results.items():
        print(pose, result)
    OUT.mkdir(parents=True, exist_ok=True)
    model.save(str(OUT / "final"))
    print("saved", OUT / "final.zip")


if __name__ == "__main__":
    main()
