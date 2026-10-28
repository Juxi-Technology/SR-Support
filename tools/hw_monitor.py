"""Background monitor for the SR-Support B-line robot on COM27.

Keeps the serial port open (opening it resets the ESP32 via DTR) and appends
a compact telemetry summary plus every state event to logs/hw_monitor.log.
Flags any commanded joint angle outside the legal servo envelope:

  shoulder  [-1.07, +2.07] rad  (180 deg total after the horn re-index)
  elbow     [-1.55, +1.55] rad  (177.6 deg total)

Run:  .venv-pio/Scripts/python.exe tools/hw_monitor.py [PORT]
Stop: close the window / Ctrl-C.
"""

from __future__ import annotations

import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import serial

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "hw_monitor.log"

SHOULDER_MIN, SHOULDER_MAX = -1.07, 2.07
ELBOW_MAX = 1.55
SUMMARY_EVERY_S = 5.0

LINE = re.compile(
    r"up\s+(\S+)\s+(\S+)\s+(\S+).*w\s+(\S+)\s+(\S+)\s+(\S+)"
    r".*q\s+(\S+)\s+(\S+).*\|\s+(\w+)")
EVENT_KEYS = ("armed", "disarmed", "pump", "push", "stand", "fall", "IMU",
              "roll-up", "getup", "executor")


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "COM27"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    s = serial.Serial(port, 115200, timeout=0.2)
    last_summary = 0.0
    buf = ""
    violations = 0
    frozen = 0
    last_sig = None
    print(f"monitoring {port} -> {LOG}")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"--- monitor start {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
        while True:
            try:
                data = s.read(1024)
            except Exception:
                data = b""
            if not data:
                continue
            buf += data.decode("utf-8", "replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if any(k in line for k in EVENT_KEYS):
                    f.write(f"{datetime.now():%H:%M:%S} EVENT {line}\n")
                    f.flush()
                m = LINE.match(line)
                if not m:
                    continue
                up_x, up_y, up_z = (float(m.group(1)), float(m.group(2)),
                                    float(m.group(3)))
                w_norm = math.sqrt(float(m.group(4)) ** 2 + float(m.group(5)) ** 2
                                   + float(m.group(6)) ** 2)
                q1, q2 = float(m.group(7)), float(m.group(8))
                mode = m.group(9)
                bad = (q1 < SHOULDER_MIN - 0.02 or q1 > SHOULDER_MAX + 0.02
                       or abs(q2) > ELBOW_MAX + 0.02)
                now = time.time()
                if bad:
                    violations += 1
                    f.write(f"{datetime.now():%H:%M:%S} !! VIOLATION q={q1:+.2f} "
                            f"{q2:+.2f} up_z={up_z:+.2f} mode={mode}\n")
                    f.flush()
                elif now - last_summary >= SUMMARY_EVERY_S:
                    last_summary = now
                    f.write(f"{datetime.now():%H:%M:%S} "
                            f"up=({up_x:+.2f},{up_y:+.2f},{up_z:+.2f}) "
                            f"q={q1:+.2f} {q2:+.2f} w={w_norm:.1f} {mode} "
                            f"(violations {violations})\n")
                    f.flush()
                    sig = (round(up_z, 2), round(q1, 2), round(q2, 2),
                           round(w_norm, 1), mode)
                    if sig == last_sig:
                        frozen += 1
                    else:
                        frozen = 0
                        last_sig = sig
                    if frozen == 4 and up_z < 0.9:
                        f.write(f"{datetime.now():%H:%M:%S} !! SUSPECT FREEZE: "
                                f"telemetry unchanged for 20 s while down\n")
                        f.flush()


if __name__ == "__main__":
    main()
