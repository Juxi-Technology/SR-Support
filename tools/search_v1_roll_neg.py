"""Search a sim-only roll_neg get-up sequence for the v1 CAD model.

The deployed roll_neg reference is hardware-specific (arm over the top + pose
re-plan) and does not transfer to MuJoCo. This searches a sim reference on
the v1 model (training/b_line/assets/robot_v1.xml) with the same
reference+feedback executor, then evolves the best candidates.

Usage:
  python tools/search_v1_roll_neg.py --random 800 --rounds 12 --pop 240 --workers 14
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv, Q_HI, Q_LO  # noqa: E402
from training.b_line.getup_executor import GetupExecutor  # noqa: E402

XML_V1 = ROOT / "training/b_line/assets/robot_v1.xml"
POSE = "roll_neg"
MAX_STEPS = 600
OUT = ROOT / "logs" / "search_v1_roll_neg.json"

# sim roll_pos reference (works on v1) and the hardware roll_neg reference
SEEDS = [
    [[2.0, -0.8], [0.0, -0.8], [0.0, 0.0]],
    [[2.0, -0.8], [2.0, -0.8], [2.0, -0.8], [2.0, -0.8], [0.0, -0.8], [0.0, 0.0]],
]


def structured():
    q1 = [-1.07, -0.54, 0.0, 0.54, 1.07, 1.60, 2.00]
    q2 = [-1.55, -0.8, 0.0, 0.8, 1.55]
    out = []
    for a in q1:
        for b in q2:
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


def eval_seq(seq):
    no_flip = os.environ.get("V1_NO_FLIP") == "1"
    seq = np.asarray(seq, dtype=np.float64)
    env = B39GetupEnv(fallen_poses=(POSE,), xml_path=XML_V1)
    env.reset(options={"pose": POSE})
    min_upz = 1.0
    ex = GetupExecutor(POSE)
    ex.sequence = seq
    ex.support = seq[-2] if len(seq) > 1 else np.zeros(2)
    obs = env._obs()
    info = {}
    ok = False
    for _ in range(MAX_STEPS):
        obs, _, term, trunc, info = env.step(ex.action(env, obs))
        upz = env.data.xmat[env.foot_body_id].reshape(3, 3)[2][2]
        if upz < min_upz:
            min_upz = float(upz)
        if term or trunc:
            ok = bool(term)
            break
    up = float(info.get("upright", -9.0))
    pen = float(info.get("pen", 0.0))
    steps = env.step_count
    env.close()
    fitness = 1000.0 * ok + 100.0 * up - 50.0 * max(0.0, -pen - 0.005)
    if no_flip:
        fitness -= 300.0 * max(0.0, -0.20 - min_upz)
    return {"seq": seq.tolist(), "ok": bool(ok), "up": up, "steps": int(steps),
            "min_upz": min_upz, "fitness": float(fitness)}


def key(r):
    return (r["fitness"], r["ok"], r["up"])


def mutate(seq, rng):
    seq = np.array(seq, dtype=np.float64)
    n = len(seq)
    r = rng.random()
    if r < 0.12 and n < 6:
        idx = int(rng.integers(1, n))
        seq = np.insert(seq, idx, rng.uniform(Q_LO, Q_HI), axis=0)
    elif r < 0.2 and n > 3:
        idx = int(rng.integers(1, n - 1))
        seq = np.delete(seq, idx, axis=0)
    else:
        k = int(rng.integers(1, 3))
        idxs = rng.choice(np.arange(n - 1), size=min(k, n - 1), replace=False)
        seq[idxs] += rng.normal(0.0, rng.uniform(0.1, 0.45), size=(len(idxs), 2))
    seq[:, 0] = np.clip(seq[:, 0], Q_LO[0], Q_HI[0])
    seq[:, 1] = np.clip(seq[:, 1], Q_LO[1], Q_HI[1])
    seq[-1] = 0.0
    return seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--random", type=int, default=800)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--pop", type=int, default=240)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--no-flip", action="store_true",
                    help="penalise the body rolling past inverted")
    args = ap.parse_args()
    if args.no_flip:
        os.environ["V1_NO_FLIP"] = "1"

    cands = SEEDS + structured() + random_candidates(args.seed, args.random)
    print(f"evaluating {len(cands)} candidates on v1 ...", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(eval_seq, cands))
    best = max(results, key=key)
    print(f"stage1 best: ok={best['ok']} up={best['up']:+.2f} "
          f"seq={np.round(np.asarray(best['seq']), 2).tolist()}", flush=True)

    rng = np.random.default_rng(args.seed + 1)
    for rnd in range(args.rounds):
        if best["ok"]:
            break
        mutants = [mutate(best["seq"], rng).tolist() for _ in range(args.pop)]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            res = list(pool.map(eval_seq, mutants))
        cand = max(res, key=key)
        if key(cand) > key(best):
            best = cand
            print(f"round {rnd}: ok={best['ok']} up={best['up']:+.2f} "
                  f"steps={best['steps']} seq={np.round(np.asarray(best['seq']), 3).tolist()}",
                  flush=True)
    print("\nBEST:", "ok" if best["ok"] else "FAIL", "up=%.2f" % best["up"])
    print(np.round(np.asarray(best["seq"]), 6).tolist())
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(best, indent=1), encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
