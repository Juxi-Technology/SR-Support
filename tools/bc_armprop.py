"""Behavior cloning of the arm-prop stand-up, then evaluate.

Demonstrations come from the trajectory-search plan (shoulder 1.86, elbow
0.83, hold 10, retract 0.0328) rolled out from many random arm-prop starts in
the 0.2 ms contact model. The existing PPO policy is supervised on the
(observation, action) pairs, then evaluated with the policy alone (no
scripted routine).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.selfright_env import SelfRightEnv

MODEL = ROOT / "training/b_line/models/ppo_b39_rq/final.zip"
OUT = ROOT / "training/b_line/models/ppo_b39_ap_bc"
PUSH, ELBOW = 1.8628, 0.80   # elbow stays inside the policy's q2 cap (0.8)
RATE, HOLD, RETRACT, PAUSE = 0.0367, 10, 0.0328, 0.920
ACT_DELTA = 0.08
N_EPISODES = 200


def demo_episode(env, seed):
    obs, _ = env.reset(seed=seed)
    q = env._prev_cmd.copy()
    up = float(env._up_body()[2])
    target = np.array([PUSH, ELBOW])
    phase = "push"
    hold = 0
    rows = []
    for t in range(240):
        q = env._prev_cmd.copy()
        if phase == "push":
            delta = target - q
            action = np.clip(delta / ACT_DELTA, -RATE / ACT_DELTA, RATE / ACT_DELTA)
            if np.max(np.abs(delta)) < 1e-3:
                phase = "hold"
                hold = 0
        elif phase == "hold":
            action = np.zeros(2)
            hold += 1
            if hold >= HOLD:
                phase = "retract"
        else:
            if up >= PAUSE:
                action = np.clip(-q / ACT_DELTA, -RETRACT / ACT_DELTA,
                                 RETRACT / ACT_DELTA)
            else:
                action = np.clip((target - q) / ACT_DELTA, 0.0,
                                 2.0 * RETRACT / ACT_DELTA)
            if np.max(np.abs(q)) < 0.02:
                action = np.zeros(2)
        rows.append((obs.copy(), action.copy()))
        obs, _, te, tr, info = env.step(action)
        up = float(info["up_z"])
        if up < 0.5:
            return []
        if phase == "retract" and np.max(np.abs(env._prev_cmd)) < 0.02:
            break
    q = env._prev_cmd
    if not (up > 0.9 and np.max(np.abs(q)) < 0.15):
        return []
    # One extra zero-action sample at the final stand.
    rows.append((obs.copy(), np.zeros(2)))
    return rows


def evaluate(env, policy, n=20):
    oks = 0
    finals = []
    for ep in range(n):
        obs, _ = env.reset(seed=5000 + ep)
        for t in range(240):
            action, _ = policy.predict(obs, deterministic=True)
            obs, _, _, _, info = env.step(action)
            if info["up_z"] < 0.5:
                break
        ok = info["up_z"] > 0.9 and np.max(np.abs(env._prev_cmd)) < 0.35
        oks += int(ok)
        finals.append((round(float(info["up_z"]), 2),
                       np.round(env._prev_cmd, 2).tolist(), ok))
    return oks, finals


def main():
    env = SelfRightEnv(robot="b39rq_ap_sr5", domain_randomization=False,
                       random_init=True, seed=0)
    obs_list, act_list = [], []
    made = 0
    for ep in range(N_EPISODES):
        rows = demo_episode(env, seed=7000 + ep)
        if rows:
            made += 1
            obs_list.extend(r[0] for r in rows)
            act_list.extend(r[1] for r in rows)
    env.close()
    obs = np.asarray(obs_list, dtype=np.float32)
    act = np.asarray(act_list, dtype=np.float32)
    print(f"demos: {made}/{N_EPISODES} succeeded, samples {len(obs)}")

    model = PPO.load(str(MODEL), device="cpu")
    policy = model.policy
    opt = torch.optim.Adam(
        list(policy.mlp_extractor.policy_net.parameters())
        + list(policy.action_net.parameters()), lr=1e-3)
    obs_t = torch.as_tensor(obs)
    act_t = torch.as_tensor(act)
    n = len(obs)
    for epoch in range(80):
        perm = torch.randperm(n)
        tot = 0.0
        for i in range(0, n, 256):
            idx = perm[i:i + 256]
            features = policy.extract_features(obs_t[idx])
            latent = policy.mlp_extractor.policy_net(features)
            mean = policy.action_net(latent)
            loss = F.mse_loss(mean, act_t[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += float(loss) * len(idx)
        if epoch % 10 == 0 or epoch == 79:
            print(f"epoch {epoch}: mse {tot / n:.5f}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    model.save(str(OUT / "final"))
    print("saved", OUT / "final.zip")

    # Evaluate the BC policy alone (no routine) from fresh arm-prop starts.
    env = SelfRightEnv(robot="b39rq_ap_sr5", domain_randomization=False,
                       random_init=True, seed=0)
    oks, finals = evaluate(env, policy, n=20)
    env.close()
    print(f"BC policy alone: {oks}/20 ok")
    for f in finals[:10]:
        print("  ", f)


if __name__ == "__main__":
    main()
