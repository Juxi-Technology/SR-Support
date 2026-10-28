"""Hardware bring-up check for the B-line robot over the USB serial port.

Examples (from the repository root, PlatformIO Python has pyserial):
  .venv-pio/Scripts/python.exe tools/hw_check.py
  .venv-pio/Scripts/python.exe tools/hw_check.py --center
  .venv-pio/Scripts/python.exe tools/hw_check.py --self-test
  .venv-pio/Scripts/python.exe tools/hw_check.py --manual 1
  .venv-pio/Scripts/python.exe tools/hw_check.py --tilt 15

--tilt logs the IMU for N seconds; tilt/pick up the robot by hand while it
runs, then read the printed up-vector and gyro ranges.
"""

from __future__ import annotations

import argparse
import math
import re
import time

import serial

UP_RE = re.compile(
    r"up\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s*\|\s*w\s+"
    r"([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+).*?\|\s*(\w+)\s*$"
)


def parse_lines(text: str):
    out = []
    for line in text.splitlines():
        m = UP_RE.search(line.strip())
        if m:
            vals = [float(x) for x in m.groups()[:6]]
            out.append((vals[:3], vals[3:], m.group(7)))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="B-line hardware check")
    p.add_argument("--port", default="COM27")
    p.add_argument("--center", action="store_true", help="send r: re-arm at neutral")
    p.add_argument("--self-test", action="store_true", dest="self_test",
                   help="send t: both joints +0.5 / -0.5 / neutral")
    p.add_argument("--manual", choices=list("01234"),
                   help="1/2 shoulder +/-0.5, 3/4 elbow +/-0.5, 0 neutral")
    p.add_argument("--tilt", type=float, default=0.0,
                   help="log the IMU for N s; tilt the robot by hand")
    args = p.parse_args()

    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = 115200
    ser.timeout = 0.2
    ser.dtr = False
    ser.rts = False
    ser.open()
    time.sleep(0.2)

    def read(seconds: float) -> str:
        buf = b""
        t0 = time.time()
        while time.time() - t0 < seconds:
            buf += ser.read(512)
        return buf.decode(errors="replace")

    try:
        if args.center:
            ser.write(b"r")
            print(read(1.0).strip())
        if args.self_test:
            ser.write(b"t")
            print(read(4.5).strip())
        if args.manual is not None:
            ser.write(args.manual.encode())
            print(read(1.2).strip())

        if args.tilt > 0:
            ser.reset_input_buffer()
            text = read(args.tilt)
            samples = parse_lines(text)
            if not samples:
                print("no telemetry; check port/baud and the firmware")
                return
            ups = [s[0] for s in samples]
            ws = [s[1] for s in samples]
            print(f"samples={len(samples)} state={samples[-1][2]}")
            for name, idx in (("up_x", 0), ("up_y", 1), ("up_z", 2)):
                vals = [u[idx] for u in ups]
                print(f"{name}: min={min(vals):+.2f} max={max(vals):+.2f}")
            tilt = [math.degrees(math.acos(max(-1.0, min(1.0, u[2])))) for u in ups]
            print(f"tilt: min={min(tilt):.1f} deg max={max(tilt):.1f} deg")
            print(f"|gyro| max={max(math.sqrt(sum(x * x for x in w)) for w in ws):.1f} rad/s")
            if max(tilt) - min(tilt) < 5.0:
                print("WARN: tilt barely changed; IMU may be stuck or the robot was not moved")
        elif not (args.center or args.self_test or args.manual is not None):
            print(read(0.6).strip())
    finally:
        ser.close()


if __name__ == "__main__":
    main()
