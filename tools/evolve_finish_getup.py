"""Evolutionary refinement of get-up references with a strict finish test.

Every candidate is rolled out with the deployed waypoint schedule (20 ticks
per waypoint), then the arm is retracted to neutral at the deployed rate and
the robot must stay standing on its own base. This rejects the "balance on
the arm" exploit that a pure up-Z fitness rewards.

Usage:
  python tools/evolve_finish_getup.py --pose roll_neg \
      --seed-file logs/robust_search_roll_neg.json --scale 2.0 \
      --rounds 14 --pop 240 --workers 14
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from search_robust_getup import make_env  # noqa: E402

STEPS_PER_WP = 20
RETRACT_RATE = 0.033
HOLD_TICKS = 50
GOAL_TICKS = 30


def eval_finish(job):
    pose, seq, scale = job
    seq = np.asarray(seq, dtype=np.float64)
    env = make_env(pose, scale)
    env.reset(options={"pose": pose})
    prev = np.zeros(2)
    for wp in seq:
        for i in range(STEPS_PER_WP):
            t = (i + 1) / STEPS_PER_WP
            ctrl = (1.0 - t) * prev + t * wp
            env.step(np.clip((ctrl - env.target) / env.target_delta,
                             -1.0, 1.0))
        prev = wp
    # Retract to neutral at the deployed rate, like the executor's final phase
    # when the body is upright (no pause/re-plant allowed here).
    for _ in range(120):
        if float(np.max(np.abs(env.target))) < 0.02:
            break
        ctrl = env.target + np.clip(-env.target, -RETRACT_RATE, RETRACT_RATE)
        env.step(np.clip((ctrl - env.target) / env.target_delta, -1.0, 1.0))
    ups = []
    info = {}
    term = False
    for _ in range(HOLD_TICKS):
        obs, _, term, trunc, info = env.step(np.zeros(2))
        ups.append(float(info.get("upright", -9.0)))
        if term or trunc:
            break
    tail = ups[-GOAL_TICKS:] if len(ups) >= GOAL_TICKS else ups
    min_tail = min(tail) if tail else -9.0
    servo = np.max(np.abs(info.get("servo_angles", [9.0, 9.0])))
    success = bool(term) or bool(min_tail > 0.95 and servo < 0.12)
    fitness = (1000.0 * float(term) + 300.0 * float(min_tail > 0.95)
               + 100.0 * min_tail + float(np.mean(tail)))
    env.close()
    return {
        "seq": seq.tolist(),
        "success": success,
        "term": bool(term),
        "min_tail": float(min_tail),
        "up_final": ups[-1] if ups else -9.0,
        "servo_max": float(servo),
        "fitness": fitness,
    }


def key(res):
    return (res["fitness"], res["success"], res["min_tail"], res["up_final"])


def mutate(seq, rng):
    seq = np.array(seq, dtype=np.float64)
    n = len(seq)
    r = rng.random()
    if r < 0.12 and n < 6:
        idx = int(rng.integers(1, n))
        new_wp = rng.uniform([-1.07, -1.55], [2.07, 1.55])
        seq = np.insert(seq, idx, new_wp, axis=0)
    elif r < 0.2 and n > 3:
        idx = int(rng.integers(1, n - 1))
        seq = np.delete(seq, idx, axis=0)
    else:
        k = int(rng.integers(1, 3))
        idxs = rng.choice(np.arange(n - 1), size=min(k, n - 1), replace=False)
        sigma = float(rng.uniform(0.1, 0.45))
        seq[idxs] += rng.normal(0.0, sigma, size=(len(idxs), 2))
    seq[:, 0] = np.clip(seq[:, 0], -1.07, 2.07)
    seq[:, 1] = np.clip(seq[:, 1], -1.55, 1.55)
    seq[-1] = 0.0
    return seq


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pose", required=True)
    p.add_argument("--seed-file", required=True)
    p.add_argument("--scale", type=float, default=2.0)
    p.add_argument("--rounds", type=int, default=14)
    p.add_argument("--pop", type=int, default=240)
    p.add_argument("--workers", type=int, default=14)
    p.add_argument("--seed", type=int, default=5)
    args = p.parse_args()

    data = json.loads(Path(args.seed_file).read_text(encoding="utf-8"))
    seeds = [r["seq"] for r in data["results"][:8]]
    rng = np.random.default_rng(args.seed)
    jobs = [(args.pose, seq, args.scale) for seq in seeds]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(eval_finish, jobs))
    best = max(results, key=key)
    print(f"seed best fitness={best['fitness']:.2f} min_tail={best['min_tail']:+.2f} "
          f"servo={best['servo_max']:+.2f} succ={best['success']}", flush=True)

    for rnd in range(args.rounds):
        mutants = [mutate(best["seq"], rng) for _ in range(args.pop)]
        mutants.append(np.asarray(best["seq"]))
        jobs = [(args.pose, m.tolist(), args.scale) for m in mutants]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(eval_finish, jobs, chunksize=2))
        cand = max(results, key=key)
        if key(cand) > key(best):
            best = cand
            print(f"round {rnd}: new best fitness={best['fitness']:.2f} "
                  f"min_tail={best['min_tail']:+.2f} servo={best['servo_max']:+.2f} "
                  f"succ={best['success']}", flush=True)
        else:
            print(f"round {rnd}: no improvement", flush=True)
        if best["success"]:
            break
    seq = np.round(np.asarray(best["seq"]), 6).tolist()
    print("\nBEST")
    print(f"success={best['success']} min_tail={best['min_tail']:+.2f} "
          f"servo={best['servo_max']:+.2f}")
    print(seq)
    out = ROOT / "logs" / f"evolve_finish_{args.pose}.json"
    out.write_text(json.dumps({"pose": args.pose, "scale": args.scale,
                               "best": best, "sequence": seq}, indent=1),
                   encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
