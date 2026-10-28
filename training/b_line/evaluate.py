"""Evaluate a trained self-righting policy.

Examples (from the repository root):
  python -m training.b_line.evaluate --robot selfrising --episodes 100
  python -m training.b_line.evaluate --robot selfrising --episodes 100 --dr --per-face
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from .selfright_env import CTRL_DT, ROBOT_SPECS, SelfRightEnv
from .stand_homer import StandHomer

ROOT = Path(__file__).resolve().parent


def _quat_axis_angle(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    s = np.sin(angle / 2.0)
    return np.array([np.cos(angle / 2.0), axis[0] * s, axis[1] * s, axis[2] * s])


FACES = {
    "on_back": _quat_axis_angle([0, 1, 0], -np.pi / 2),
    "on_front": _quat_axis_angle([0, 1, 0], np.pi / 2),
    "left_side": _quat_axis_angle([1, 0, 0], -np.pi / 2),
    "right_side": _quat_axis_angle([1, 0, 0], np.pi / 2),
}


def rollout(env, model, seed: int, options: dict | None = None,
            home: bool = False) -> tuple[bool, float | None, float]:
    obs, _ = env.reset(seed=seed, options=options)
    homer = StandHomer() if home else None
    upright = []
    ret = 0.0
    for _ in range(env.episode_steps):
        if homer is not None and homer.state != "policy":
            action = homer.action(env)
        else:
            action, _ = model.predict(obs, deterministic=True)
        obs, rew, terminated, truncated, info = env.step(action)
        if homer is not None:
            homer.update(env, info)
        ret += rew
        if home:
            q_max = float(np.max(np.abs(env._prev_cmd)))
            upright.append(bool(info["up_z"] > 0.9 and info["height_ok"] and q_max < 0.12))
        else:
            upright.append(bool(info["upright"]))
        if truncated:
            break
    tail = np.array(upright[-25:], dtype=float)
    ok = bool(tail.mean() >= 0.9)
    t_stand = None
    for t in range(len(upright)):
        if all(upright[t:]):
            t_stand = t * CTRL_DT
            break
    return ok, t_stand, ret


def summarize(rows: list[dict]) -> dict:
    successes = sum(r["success"] for r in rows)
    times = [r["t_stand"] for r in rows if r["t_stand"] is not None]
    return {
        "episodes": len(rows),
        "success_rate": successes / max(len(rows), 1),
        "mean_time_to_stand_s": float(np.mean(times)) if times else None,
        "median_time_to_stand_s": float(np.median(times)) if times else None,
        "mean_return": float(np.mean([r["return"] for r in rows])) if rows else None,
    }


def run(
    model_path: str,
    episodes: int,
    dr: bool,
    random_init: bool,
    seed: int,
    robot: str,
    per_face: bool = False,
    home: bool = False,
) -> dict:
    env = SelfRightEnv(
        robot=robot, domain_randomization=dr, random_init=random_init, seed=seed
    )
    model = PPO.load(model_path, device="cpu")

    rows = []
    for ep in range(episodes):
        ok, t_stand, ret = rollout(env, model, seed + ep, home=home)
        rows.append({"episode": ep, "success": ok, "t_stand": t_stand, "return": ret})

    result = {
        "model": str(model_path),
        "robot": robot,
        "domain_randomization": dr,
        "random_init": random_init,
        "stand_homing": home,
        **summarize(rows),
        "episodes_detail": rows,
    }

    if per_face:
        per_face_rows = {}
        for i, (name, quat) in enumerate(FACES.items()):
            face_rows = []
            for ep in range(max(5, episodes // 5)):
                ok, t_stand, ret = rollout(
                    env,
                    model,
                    seed + 1000 * (i + 1) + ep,
                    options={"quat": quat, "arm_q": [0.0, 0.0]},
                    home=home,
                )
                face_rows.append(
                    {"episode": ep, "success": ok, "t_stand": t_stand, "return": ret}
                )
            per_face_rows[name] = {"detail": face_rows, **summarize(face_rows)}
        result["per_face"] = per_face_rows

    env.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=str, default=None)
    p.add_argument("--robot", choices=sorted(ROBOT_SPECS), default="selfrising_sr5")
    p.add_argument("--episodes", type=int, default=100)
    p.add_argument("--dr", action="store_true", help="enable domain randomization")
    p.add_argument("--nominal-init", action="store_true", help="start upright instead of fallen")
    p.add_argument("--per-face", action="store_true", help="also evaluate each canonical fallen face")
    p.add_argument("--home", action="store_true",
                   help="apply the stand-homing controller and require the arm-vertical end pose")
    p.add_argument("--seed", type=int, default=20_000)
    p.add_argument("--out", type=str, default=None)
    args = p.parse_args()

    model_path = args.model or str(ROOT / f"models/ppo_{args.robot}/final.zip")
    result = run(
        model_path,
        args.episodes,
        args.dr,
        not args.nominal_init,
        args.seed,
        args.robot,
        per_face=args.per_face,
        home=args.home,
    )
    tag = f"{args.robot}_{'dr' if args.dr else 'nominal'}{'_home' if args.home else ''}"
    out = Path(args.out) if args.out else ROOT / f"models/eval_{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(
        f"{tag}: success {result['success_rate'] * 100:.1f}% over {args.episodes} episodes, "
        f"mean stand time {result['mean_time_to_stand_s']}, "
        f"mean return {result['mean_return']:.1f} -> {out}"
    )
    if "per_face" in result:
        for name, s in result["per_face"].items():
            print(f"  {name:12s} {s['success_rate'] * 100:5.1f}%  (n={s['episodes']})")


if __name__ == "__main__":
    main()
