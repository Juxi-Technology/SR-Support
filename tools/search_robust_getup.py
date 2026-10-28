"""Robust get-up reference search against arm-mass uncertainty.

The real b39 arm is heavier than the current model: scaling arm1/arm2 mass by
~2x reproduces the hardware roll_neg failure exactly (the body is rolled over
its top instead of yawing to the pitch axis, and the sequence ends kneeling).
This tool searches waypoint sequences with the deployed executor logic and
requires a candidate to stand the robot up across an arm-mass ensemble, so
the reference is not tuned to one uncertain mass value.

Usage:
  python tools/search_robust_getup.py --pose roll_neg --scales 1.5 2.0 2.5 \
      --random-count 800 --workers 12
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

import mujoco  # noqa: E402

from training.b_line.getup_env import B39GetupEnv, Q_HI, Q_LO  # noqa: E402
from training.b_line.getup_executor import GetupExecutor  # noqa: E402

MAX_STEPS = 260
OUT_DIR = ROOT / "logs"


def structured_candidates():
    q1_vals = [-1.07, -0.54, 0.0, 0.54, 1.07, 1.60, 2.00]
    q2_vals = [-1.55, -0.8, 0.0, 0.8, 1.55]
    out = []
    for a in q1_vals:
        for b in q2_vals:
            out.append([[a, b], [0.0, b], [0.0, 0.0]])
            out.append([[a, b], [a, 0.0], [0.0, 0.0]])
            out.append([[0.0, b], [a, b], [0.0, 0.0]])
    return out


def random_candidates(seed, count):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(count):
        n = int(rng.integers(3, 6))
        seq = rng.uniform(Q_LO, Q_HI, size=(n, 2))
        seq[-1] = 0.0
        out.append(seq.tolist())
    return out


def make_env(pose, scale):
    env = B39GetupEnv(fallen_poses=(pose,))
    if scale != 1.0:
        m = env.model
        for name in ("arm1", "arm2"):
            bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
            m.body_mass[bid] *= scale
            m.body_inertia[bid] *= scale
    return env


def eval_candidate(job):
    pose, seq, scales = job
    seq = np.asarray(seq, dtype=np.float64)
    rows = []
    for scale in scales:
        env = make_env(pose, scale)
        env.reset(options={"pose": pose})
        ex = GetupExecutor(pose, max_switches=0)
        ex.sequence = seq
        ex.support = seq[-2] if len(seq) > 1 else np.zeros(2)
        obs = env._obs()
        info = {}
        ok = False
        for _ in range(MAX_STEPS):
            obs, _, term, trunc, info = env.step(ex.action(env, obs))
            if term or trunc:
                ok = bool(term)
                break
        rows.append({
            "scale": scale,
            "ok": bool(ok),
            "up": float(info.get("upright", -9.0)),
            "steps": env.step_count,
            "pen": float(info.get("pen", 0.0)),
        })
        env.close()
    n_ok = sum(r["ok"] for r in rows)
    min_up = min(r["up"] for r in rows)
    mean_up = float(np.mean([r["up"] for r in rows]))
    return {
        "seq": seq.tolist(),
        "rows": rows,
        "n_ok": n_ok,
        "min_up": min_up,
        "mean_up": mean_up,
        "fitness": 1000.0 * n_ok + 100.0 * min_up + mean_up,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pose", required=True)
    p.add_argument("--scales", type=float, nargs="+", default=[2.0])
    p.add_argument("--random-count", type=int, default=600)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--max-candidates", type=int, default=0,
                   help="0 = all; otherwise evaluate the first N candidates")
    args = p.parse_args()

    cands = structured_candidates() + random_candidates(args.seed,
                                                       args.random_count)
    if args.max_candidates:
        cands = cands[:args.max_candidates]
    jobs = [(args.pose, seq, args.scales) for seq in cands]
    print(f"{args.pose}: {len(jobs)} candidates x scales {args.scales}",
          flush=True)
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(eval_candidate, jobs, chunksize=4)):
            results.append(res)
            if (i + 1) % 50 == 0:
                best = max(results, key=lambda r: r["fitness"])
                print(f"  {i+1}/{len(jobs)} best n_ok={best['n_ok']} "
                      f"min_up={best['min_up']:+.2f} "
                      f"seq={np.round(np.asarray(best['seq']), 2).tolist()}",
                      flush=True)
    results.sort(key=lambda r: r["fitness"], reverse=True)
    print("\nTOP CANDIDATES")
    for r in results[:args.top]:
        print(f"  fitness={r['fitness']:.2f} n_ok={r['n_ok']}/{len(r['rows'])} "
              f"min_up={r['min_up']:+.2f} rows={r['rows']}")
        print(f"    seq={np.round(np.asarray(r['seq']), 4).tolist()}")
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"robust_search_{args.pose}.json"
    out.write_text(json.dumps({"pose": args.pose, "scales": args.scales,
                               "results": results[:max(args.top, 50)]},
                              indent=1), encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
