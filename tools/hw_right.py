"""Scripted hardware righting from the side pose (PTK7452, no policy).

Sends manual joint targets over serial and checks the IMU after each step.
This is the sequence that worked on the assembled SelfRisingRobot print on
2026-10-22; it assumes the robot is lying on its side (body +X up, up_z ~ 0).

  python tools/hw_right.py --port COM27

It is a bring-up/demo aid, not the final controller. Stop if the arm binds or
a servo stalls (the PTK has no position feedback).
"""

from __future__ import annotations

import argparse
import re
import statistics
import time

import serial

SEQ = [
    (0.50, -1.55),
    (-1.55, -1.55),
    (-1.55, 1.55),
    (1.55, -1.55),
    (1.55, 0.00),
    (-0.50, -1.55),
]

UP_RE = re.compile(r"up\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+).*?\|\s*(\w+)\s*$")


def main() -> None:
    p = argparse.ArgumentParser(description="Scripted hardware righting")
    p.add_argument("--port", default="COM27")
    p.add_argument("--hold", type=float, default=1.3, help="seconds per pose")
    args = p.parse_args()

    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = 115200
    ser.timeout = 0.2
    ser.dtr = False
    ser.rts = False
    ser.open()
    time.sleep(0.3)

    def read(sec: float) -> str:
        buf = b""
        t0 = time.time()
        while time.time() - t0 < sec:
            buf += ser.read(512)
        return buf.decode(errors="replace")

    def up_mean(sec: float = 0.6):
        text = read(sec)
        rows = [m for m in UP_RE.finditer(text)]
        if not rows:
            return None, None
        vals = [tuple(map(float, m.groups()[:3])) for m in rows]
        mean = tuple(round(statistics.mean(v[i] for v in vals), 2) for i in range(3))
        return mean, rows[-1].group(4)

    def target(q1: float, q2: float) -> None:
        ser.write(f"m {q1:.2f} {q2:.2f}\n".encode())
        time.sleep(args.hold)

    up, state = up_mean(0.8)
    print(f"start: up={up} state={state}")
    if up is None:
        print("no telemetry; check port/firmware")
        ser.close()
        return
    if up[2] > 0.9:
        print("already upright; nothing to do")
        ser.write(b"r")
        time.sleep(0.5)
        ser.close()
        return

    standing = False
    for q1, q2 in SEQ:
        target(q1, q2)
        up, _ = up_mean(0.5)
        print(f"  m {q1:+.2f} {q2:+.2f} -> up={up}")
        if up is not None and up[2] > 0.85:
            standing = True
            break

    if standing:
        target(0.0, 0.0)
        up, _ = up_mean(0.8)
        print(f"  m  0.00  0.00 -> up={up}")
        ser.write(b"r")
        time.sleep(0.5)
        up, state = up_mean(0.6)
        print(f"final: up={up} state={state}")
        print("OK: standing; arm at neutral" if up and up[2] > 0.85 else
              "WARN: homed but not upright")
    else:
        print("FAIL: sequence did not right the robot; send r to center")
        ser.write(b"r")
        time.sleep(0.5)
    ser.close()


if __name__ == "__main__":
    main()
