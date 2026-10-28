"""Search a stand-up trajectory from the arm-prop pose.

The policy parks at up_z~0.93, q~(1.48,0.14); the only current escape is the
PushStand push to 1.9 rad then a slow retract. This script samples low-
dimensional waypoint plans (shoulder target, elbow target, rates, hold,
retract rate) and rolls them out in the 0.25 ms contact model, scoring final
stand pose, no arm penetration, and time. If no sampled plan reaches a clean
vertical stand, the geometry cannot do it from this pose.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.selfright_env import SelfRightEnv

OUT = ROOT / "logs" / "standup_search.json"
N_SAMPLES = 160
PEN_TOL = 0.005


def rollout(env, plan, seed):
    obs, _ = env.reset(seed=seed)
    d = env.unwrapped
    q = d._prev_cmd.copy()
    up = float(d._up_body()[2])
    pen_min = 0.0
    t = 0
    q0 = q.copy()
    up0 = up

    def ramp(target, rate, max_ticks):
        nonlocal q, up, pen_min, t
        target = np.asarray(target, dtype=float)
        for _ in range(max_ticks):
            q = d._prev_cmd.copy()
            cmd = q + np.clip(target - q, -rate, rate)
            d.ctrl_override = cmd
            obs, _, _, _, info = env.step(np.zeros(2))
            pen_min = min(pen_min, d.arm_penetration())
            up = float(info["up_z"]); t += 1
            if up < 0.5:
                return False
            if np.max(np.abs(target - d._prev_cmd)) < 1e-3:
                break
        return True

    # Stage 1: shoulder/elbow to the support pose.
    if not ramp([plan["push"], plan["elbow"]], plan["push_rate"], 400):
        return {"ok": False, "reason": "fell_push", "up": up, "q": d._prev_cmd.tolist(),
                "pen": pen_min, "t": t}
    # Hold.
    target = np.array([plan["push"], plan["elbow"]], dtype=float)
    for _ in range(plan["hold"]):
        d.ctrl_override = target.copy()
        obs, _, _, _, info = env.step(np.zeros(2))
        pen_min = min(pen_min, d.arm_penetration())
        up = float(info["up_z"]); t += 1
        if up < 0.5:
            return {"ok": False, "reason": "fell_hold", "up": up, "q": d._prev_cmd.tolist(),
                    "pen": pen_min, "t": t}
    # Stage 2: retract to vertical; if the body sags, re-plant and resume.
    for _ in range(1000):
        q = d._prev_cmd.copy()
        if up >= plan["pause"]:
            cmd = q + np.clip(-q, -plan["retract_rate"], plan["retract_rate"])
        else:
            cmd = q.copy()
            cmd[0] += float(np.clip(plan["push"] - q[0], 0.0, 2.0 * plan["retract_rate"]))
            cmd[1] += float(np.clip(plan["elbow"] - q[1], 0.0, 2.0 * plan["retract_rate"]))
        d.ctrl_override = cmd
        obs, _, _, _, info = env.step(np.zeros(2))
        pen_min = min(pen_min, d.arm_penetration())
        up = float(info["up_z"]); t += 1
        if up < 0.5:
            return {"ok": False, "reason": "fell_retract", "up": up, "q": d._prev_cmd.tolist(),
                    "pen": pen_min, "t": t}
        if np.max(np.abs(d._prev_cmd)) < 0.02:
            d.ctrl_override = np.zeros(2)
            obs, _, _, _, info = env.step(np.zeros(2))
            up = float(info["up_z"]); t += 1
            break
    q = d._prev_cmd.copy()
    ok = up > 0.9 and np.max(np.abs(q)) < 0.15 and pen_min > -PEN_TOL
    return {"ok": bool(ok), "reason": "stand" if ok else "final",
            "up": up, "q": q.tolist(), "pen": pen_min, "t": t,
            "start_q": q0.tolist(), "start_up": up0}


def main():
    env = SelfRightEnv(robot="b39rq_ap_sr5", domain_randomization=False,
                       random_init=True, seed=0)
    rng = np.random.default_rng(12345)
    rows = []
    for i in range(N_SAMPLES):
        plan = {
            "push": float(rng.uniform(1.45, 2.0)),
            "elbow": float(rng.uniform(0.4, 1.1)),
            "push_rate": float(rng.uniform(0.02, 0.10)),
            "hold": int(rng.integers(0, 60)),
            "retract_rate": float(rng.uniform(0.01, 0.04)),
            "pause": float(rng.uniform(0.9, 0.98)),
        }
        r = rollout(env, plan, seed=1000 + i)
        r["plan"] = plan
        rows.append(r)
        if r["ok"]:
            print(f"{i}: OK plan={plan} up={r['up']:.2f} q={np.round(r['q'],2)} "
                  f"pen={r['pen']*1000:.1f}mm t={r['t']}", flush=True)
    env.close()
    rows.sort(key=lambda r: (not r["ok"], r["pen"], r["t"]))
    OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    oks = [r for r in rows if r["ok"]]
    print(f"\n{len(oks)}/{len(rows)} feasible clean stand-ups")
    for r in oks[:5]:
        print(" best", r["plan"], "up", round(r["up"], 2), "q", np.round(r["q"], 2),
              "pen", round(r["pen"] * 1000, 1), "t", r["t"])
    if not oks:
        print("no clean plan; best finals:")
        for r in rows[:5]:
            print(" ", r["reason"], "up", round(r["up"], 2), "q", np.round(r["q"], 2),
                  "pen", round(r["pen"] * 1000, 1), "plan", r["plan"])


if __name__ == "__main__":
    main()
