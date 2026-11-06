"""Functional check of the computer-side tool environment.

Unlike a bare ``import`` test, this actually loads the robot model, steps the
MuJoCo engine and lists the serial ports, so a broken install fails here.

Run from anywhere with the project venv activated (see tutorial page 02):
  python tools/env_check.py

Exit code 0 = PASS, 1 = FAIL.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML = ROOT / "hardware" / "v1" / "robot_v1.xml"


def main() -> int:
    ap = argparse.ArgumentParser(description="Check the SR-Support tool environment")
    ap.add_argument("--xml", default=str(DEFAULT_XML), help="MuJoCo model to load")
    ap.add_argument("--steps", type=int, default=200, help="simulation steps to run")
    args = ap.parse_args()

    errors: list[str] = []

    try:
        import numpy as np
        print(f"[ok] numpy {np.__version__}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"numpy: {exc}")
        np = None

    try:
        import mujoco
        print(f"[ok] mujoco {mujoco.__version__}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"mujoco: {exc}")
        mujoco = None

    try:
        import serial
        import serial.tools.list_ports
        print(f"[ok] pyserial {serial.VERSION}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pyserial: {exc}")
        serial = None

    try:
        import gymnasium
        print(f"[ok] gymnasium {gymnasium.__version__}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"gymnasium: {exc}")

    if mujoco is not None and np is not None:
        xml = Path(args.xml)
        if not xml.exists():
            errors.append(f"model not found: {xml}")
        else:
            try:
                model = mujoco.MjModel.from_xml_path(str(xml))
                data = mujoco.MjData(model)
                for _ in range(max(1, args.steps)):
                    mujoco.mj_step(model, data)
                finite = bool(np.isfinite(data.qpos).all() and np.isfinite(data.qacc).all())
                if not finite:
                    errors.append("simulation produced non-finite state")
                else:
                    print(
                        f"[ok] model {xml.relative_to(ROOT)}: nq={model.nq} nv={model.nv} "
                        f"dt={model.opt.timestep:g}s, {args.steps} steps stable "
                        f"(root z={data.qpos[2]:.3f} m)"
                    )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"model/step: {exc}")

    if serial is not None:
        ports = list(serial.tools.list_ports.comports())
        if ports:
            for p in ports:
                print(f"[ok] serial port {p.device} ({p.description})")
        else:
            print("[--] no serial port found (plug the board in later; not a failure)")

    if errors:
        print("\nenv check: FAIL")
        for e in errors:
            print("  -", e)
        return 1
    print("\nenv check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
