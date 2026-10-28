"""Evolutionary refinement of get-up reference sequences.

Seeds from the top candidates of search_robust_getup.py and hill-climbs
waypoint sequences against the arm-mass-2x surrogate (the one that matches
the hardware roll failure). Fitness is the executor rollout: standing up
(env terminated), then final upright.

Usage:
  python tools/evolve_getup.py --pose roll_neg --seed-file logs/robust_search_roll_neg.json \
      --scale 2.0 --rounds 12 --pop 200 --workers 14
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

from search_robust_getup import eval_candidate  # noqa: E402


def mutate(seq, rng):
    seq = np.array(seq, dtype=np.float64)
    n = len(seq)
    r = rng.random()
    if r < 0.12 and n < 6:
        # insert a waypoint before the final zero
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


def key(res):
    return (res["fitness"], res["n_ok"], res["min_up"], res["mean_up"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pose", required=True)
    p.add_argument("--seed-file", required=True)
    p.add_argument("--scale", type=float, default=2.0)
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--pop", type=int, default=200)
    p.add_argument("--workers", type=int, default=14)
    p.add_argument("--seed", type=int, default=3)
    args = p.parse_args()

    data = json.loads(Path(args.seed_file).read_text(encoding="utf-8"))
    seeds = [r["seq"] for r in data["results"][:5]]
    rng = np.random.default_rng(args.seed)
    jobs = [(args.pose, seq, [args.scale]) for seq in seeds]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(eval_candidate, jobs))
    best = max(results, key=key)
    print(f"seed best fitness={best['fitness']:.2f} up={best['min_up']:+.2f} "
          f"seq={np.round(np.asarray(best['seq']), 3).tolist()}", flush=True)

    for rnd in range(args.rounds):
        mutants = [mutate(best["seq"], rng) for _ in range(args.pop)]
        mutants.append(np.asarray(best["seq"]))
        jobs = [(args.pose, m.tolist(), [args.scale]) for m in mutants]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(eval_candidate, jobs, chunksize=2))
        cand = max(results, key=key)
        if key(cand) > key(best):
            best = cand
            print(f"round {rnd}: new best fitness={best['fitness']:.2f} "
                  f"up={best['min_up']:+.2f} ok={best['n_ok']}", flush=True)
        else:
            print(f"round {rnd}: no improvement", flush=True)
        if best["n_ok"] == 1 and best["min_up"] > 0.97:
            break
    seq = np.round(np.asarray(best["seq"]), 6).tolist()
    print("\nBEST")
    print(f"fitness={best['fitness']:.2f} up={best['min_up']:+.2f} "
          f"steps={best['rows'][0]['steps']}")
    print(seq)
    out = ROOT / "logs" / f"evolve_{args.pose}.json"
    out.write_text(json.dumps({"pose": args.pose, "scale": args.scale,
                               "best": best, "sequence": seq}, indent=1),
                   encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
