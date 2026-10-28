"""STL printability checks: watertight, winding, volume, disconnected shells."""
from __future__ import annotations

import glob
import sys

import trimesh


def main(pattern: str = "STL/*.stl") -> int:
    bad = 0
    for path in sorted(glob.glob(pattern)):
        mesh = trimesh.load_mesh(path, process=True)
        parts = mesh.split(only_watertight=False)
        ok = mesh.is_watertight and mesh.is_winding_consistent and len(parts) == 1 and mesh.volume > 0
        print(
            f"{path:28s} watertight={mesh.is_watertight!s:5s} winding={mesh.is_winding_consistent!s:5s} "
            f"shells={len(parts):2d} volume={mesh.volume:9.1f} mm3 "
            f"bounds={mesh.bounds.round(2).tolist()} {'OK' if ok else 'FAIL'}"
        )
        if not ok:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "STL/*.stl"))
