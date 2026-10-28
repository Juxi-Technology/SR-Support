"""Capture the firmware's 50 Hz fast log for bring-up/diagnosis.

  .venv-pio/Scripts/python.exe tools/hw_log.py                 # hold, 3 s
  .venv-pio/Scripts/python.exe tools/hw_log.py --policy        # send g, log 3 s, then s

The log is saved under logs/ and a short summary (IMU sample repeats, q range,
up range) is printed. Use it to check the IMU output rate and whether the
policy commands are oscillating.
"""

from __future__ import annotations

import argparse
import re
import time
from datetime import datetime
from pathlib import Path

import serial

F_RE = re.compile(
    r"^F\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s*\|\s*"
    r"([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s*\|\s*"
    r"([-+0-9.]+)\s+([-+0-9.]+)\s*\|\s*(\d+)\s*\|\s*"
    r"(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)"
)


def main() -> None:
    p = argparse.ArgumentParser(description="Capture the firmware fast log")
    p.add_argument("--port", default="COM27")
    p.add_argument("--seconds", type=float, default=4.0)
    p.add_argument("--policy", action="store_true", help="send g before logging, s after")
    args = p.parse_args()

    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = 115200
    ser.timeout = 0.2
    ser.dtr = False
    ser.rts = False
    ser.open()
    time.sleep(0.2)
    ser.reset_input_buffer()

    if args.policy:
        ser.write(b"g")
        time.sleep(0.2)
    ser.write(b"l")

    buf = b""
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        buf += ser.read(512)
    if args.policy:
        ser.write(b"s")
    ser.close()

    text = buf.decode(errors="replace")
    lines = [l for l in text.splitlines() if l.startswith("F ")]
    outdir = Path("logs")
    outdir.mkdir(exist_ok=True)
    path = outdir / f"hw_fast_{datetime.now():%Y%m%d_%H%M%S}.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    rows = []
    for line in lines:
        m = F_RE.match(line.strip())
        if m:
            rows.append(([float(x) for x in m.groups()[:8]], int(m.group(9)),
                         [int(x) for x in m.groups()[9:]]))
    if not rows:
        print("no fast-log lines; check that the new firmware is flashed")
        return

    ups = [r[0][:3] for r in rows]
    qs = [r[0][6:8] for r in rows]
    raws = [r[2] for r in rows]
    repeats = sum(1 for a, b in zip(raws, raws[1:]) if a == b)
    print(f"saved {path} ({len(rows)} lines)")
    print(f"state last={rows[-1][1]}")
    print(f"up_z range: {min(u[2] for u in ups):+.2f} .. {max(u[2] for u in ups):+.2f}")
    for i, name in enumerate(("q1", "q2")):
        vals = [q[i] for q in qs]
        print(f"{name}: {min(vals):+.3f} .. {max(vals):+.3f}  (delta {max(vals)-min(vals):.3f})")
    print(f"raw IMU repeats between consecutive 50 Hz samples: {repeats}/{max(len(raws)-1,1)}")
    if repeats > (len(raws) - 1) * 0.4:
        print("WARN: IMU data changes slower than 50 Hz; the policy sees stale samples")
    if rows and max(abs(q[0]) for q in qs) > 0.01 and max(abs(q[1]) for q in qs) > 0.01:
        print("note: check q delta above for policy oscillation")


if __name__ == "__main__":
    main()
