"""Search scripted get-up target-angle sequences for the 4 cm b39 build.

Mirrors the original SelfRisingRobot search_all_getup.py: enumerate coarse
target-waypoint patterns plus random sequences, roll each one out in the
0.25/0.2 ms MuJoCo model, and keep the best sequence per fallen pose.

Outputs a JSON file per pose and prints a REFERENCE_CANDIDATES block.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv, DEFAULT_FALLEN_POSES, Q_HI, Q_LO

STEPS_PER_WP = 20   # control steps (0.4 s) per waypoint
HOLD_STEPS = 10     # zero-target hold at the end
OUT_DIR = ROOT / "logs"


def schedule(sequence):
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
    return np.clip((np.asarray(ctrl) - env.target) / env.target_delta, -1.0, 1.0)


def eval_sequence(pose, sequence):
    env = B39GetupEnv(fallen_poses=(pose,))
    obs, _ = env.reset(options={"pose": pose})
    best = {"score": -1e9}
    final = {}
    for ctrl in schedule(sequence):
        obs, _, terminated, truncated, info = env.step(scripted_action(env, ctrl))
        servo = info["servo_angles"]
        score = (info["upright"]
                 - 0.05 * float(np.sum(servo * servo))
                 - 0.02 * float(np.sum(info["target"] * info["target"]))
                 - 5.0 * max(0.0, -info["pen"] - 0.005))
        if score > best["score"]:
            best = {
                "score": float(score),
                "upright": float(info["upright"]),
                "servo_angles": servo.copy().tolist(),
                "target": info["target"].copy().tolist(),
                "goal_pose": bool(info["goal_pose"]),
                "pen": float(info["pen"]),
            }
        final = info
        if terminated or truncated:
            break
    env.close()
    return best, final


def build_candidates(seed, random_count):
    rng = np.random.default_rng(seed)
    q1_vals = [-1.07, -0.54, 0.0, 0.54, 1.07, 1.60, 2.00]
    q2_vals = [-1.55, -0.8, 0.0, 0.8, 1.55]
    candidates = []
    for a in q1_vals:
        for b in q2_vals:
            candidates.append(np.array([[a, b], [0.0, b], [0.0, 0.0]]))
            candidates.append(np.array([[a, b], [a, 0.0], [0.0, 0.0]]))
            candidates.append(np.array([[0.0, b], [a, b], [0.0, 0.0]]))
    for _ in range(random_count):
        seq = rng.uniform(Q_LO, Q_HI, size=(5, 2))
        seq[-1] = 0.0
        candidates.append(seq)
    return candidates


def search_pose(pose, seed, random_count):
    candidates = build_candidates(seed, random_count)
    best = None
    best_seq = None
    for i, seq in enumerate(candidates):
        detail, final = eval_sequence(pose, seq)
        if best is None or detail["score"] > best["score"]:
            best = detail
            best_seq = np.asarray(seq)
            print(f"{pose} new_best {i} score {best['score']:.4f} "
                  f"up {best['upright']:.3f} goal {best['goal_pose']} "
                  f"pen {best['pen']*1000:.1f}mm seq {np.round(best_seq,3).tolist()}",
                  flush=True)
            if best["goal_pose"]:
                break
    return {"pose": pose, "best": best, "sequence": best_seq.tolist()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pose", action="append", choices=list(DEFAULT_FALLEN_POSES))
    p.add_argument("--seed", type=int, default=4)
    p.add_argument("--random-count", type=int, default=300)
    args = p.parse_args()
    poses = args.pose or list(DEFAULT_FALLEN_POSES)
    OUT_DIR.mkdir(exist_ok=True)
    results = {}
    for pose in poses:
        print("POSE", pose, flush=True)
        results[pose] = search_pose(pose, args.seed, args.random_count)
        (OUT_DIR / f"search_b39_getup_{pose}.json").write_text(
            json.dumps(results[pose], indent=1), encoding="utf-8")
    print("\nREFERENCE_CANDIDATES")
    for pose, r in results.items():
        print(pose)
        print(np.round(np.asarray(r["sequence"]), 6).tolist())
    (OUT_DIR / "search_b39_getup_all.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
