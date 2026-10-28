"""Exact assembly interference checks for the two line assemblies (mm^3)."""
from __future__ import annotations

import sys
from itertools import combinations

from cadgen import read_scene
from cadgen.geometry import overlap_volume


def main() -> int:
    pairs = [
        ("arm1", "arm2"),
        ("base", "arm1"),
        ("base", "arm2"),
        ("servo_shoulder", "base"),
        ("servo_shoulder", "arm1"),
        ("servo_elbow", "arm1"),
        ("servo_elbow", "arm2"),
        ("imu_board", "base"),
    ]
    bad = 0
    for line in ("a", "b"):
        path = f"STEP/{line}_assembly.step"
        scene = read_scene(path)
        leaves = {occ.label: occ for occ in scene.leaves()}
        print(f"\n{path}: labels={sorted(leaves)}")
        shapes = {}
        for occ in leaves.values():
            solids = occ.shape().solids()
            if len(solids) != 1:
                print(f"  WARN {occ.label}: {len(solids)} solids")
            shapes[occ.label] = solids
        labels = list(shapes)
        for a, b in combinations(labels, 2):
            vol = sum(
                overlap_volume(sa, sb) for sa in shapes[a] for sb in shapes[b]
            )
            flag = ""
            if vol > 1e-3:
                flag = "  <-- INTERFERENCE"
                bad += 1
            print(f"  {a:16s} vs {b:16s}: {vol:10.4f}{flag}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
