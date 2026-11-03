"""Interactive shoulder travel recorder (live robot, operator driven).

The operator drives the shoulder step by step and watches the arm; this
tool sends the commands and records the marked ends together with the
4 Hz IMU status lines. Run it in a terminal with the servo battery and
the USB cable both connected:

    .venv/Scripts/python.exe tools/hw_shoulder_range.py

At the prompt:
    0.30 / -0.55    go to that shoulder angle in rad (elbow stays put)
    a 0.3 -0.5      absolute shoulder + elbow
    0.3 -0.5        shorthand for the same
    e 0.1           elbow only: absolute target (e alone prints it)
    e+ / e-         elbow step +-0.05      e++ / e--  step +-0.20
    + / -           step +-0.05 rad
    ++ / --         step +-0.20 rad
    m [label]       mark the current commanded angle as a limit
    z               firmware zero: the CURRENT pose becomes q = 0
    k               print the firmware PWM centers (shoulder/elbow us)
    n               neutral (0, 0)
    q               quit (goes to neutral first)

Everything lands in logs/shoulder_range_session.txt, including the marks,
so the real travel can be baked into the firmware afterwards. There is
no servo position feedback: a marked angle is the command at the moment
the arm physically stops, which is the achieved angle while stalled.
Manual-mode software limits come from config.h (Q_SHOULDER_MIN/MAX).
"""
from __future__ import annotations

import time
from datetime import datetime

import serial

PORT = "COM27"
BAUD = 115200
Q_MIN, Q_MAX = -1.6, 2.07       # config.h manual clamp

ser = serial.Serial()
ser.port = PORT
ser.baudrate = BAUD
ser.timeout = 0.05
ser.dtr = False
ser.rts = False
ser.open()
time.sleep(0.3)

log = open("logs/shoulder_range_session.txt", "a", encoding="utf-8")
log.write(f"\n# session {datetime.now():%Y-%m-%d %H:%M:%S}\n")

buf = ""
latest_up = "-"


def pump(sec: float = 0.8) -> None:
    global buf, latest_up
    t0 = time.time()
    while time.time() - t0 < sec:
        d = ser.read(4096)
        if not d:
            continue
        buf += d.decode("utf-8", "replace")
        while "\n" in buf:
            ln, buf = buf.split("\n", 1)
            ln = ln.strip()
            if not ln:
                continue
            log.write(ln + "\n")
            if ln.startswith("up "):
                latest_up = ln.split("|")[0].strip()
            elif not ln.startswith(("S ", "T ", "F ")):
                print("  [robot]", ln)   # command replies (z, k, ...)


def send(cmd: str) -> None:
    ser.write((cmd + "\n").encode())
    log.write(f">>> {cmd}\n")


q1 = 0.0
q2 = 0.0
marks: list[tuple[float, float, str]] = []


def goto(a: float, b: float | None = None) -> None:
    global q1, q2
    if b is not None:
        q2 = float(b)
    raw = float(a)
    q1 = max(Q_MIN, min(Q_MAX, raw))
    if abs(q1 - raw) > 1e-9:
        print(f"  (commanded {raw:+.3f} clamped to {q1:+.3f} by the "
              f"firmware manual limit)")
    send(f"m {q1:.3f} {q2:.3f}")
    pump()
    print(f"  shoulder {q1:+.3f} ({q1 * 57.2958:+.0f} deg)  "
          f"elbow {q2:+.3f} ({q2 * 57.2958:+.0f} deg) | {latest_up}")


send("m 0.000 0.000")
pump()
print("connected. current: shoulder +0.000 rad, elbow +0.000 rad.")
print("watch the arm; when it physically stops at an end, type: m <label>")

while True:
    try:
        line = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        line = "q"
    if not line:
        continue
    parts = line.replace(",", " ").split()
    cmd = parts[0].lower()
    try:
        if cmd in ("q", "quit", "exit"):
            goto(0.0, 0.0)
            break
        if cmd in ("n", "0"):
            goto(0.0, 0.0)
        elif cmd in ("+", "-"):
            goto(q1 + (0.05 if cmd == "+" else -0.05))
        elif cmd in ("++", "--"):
            goto(q1 + (0.20 if cmd == "++" else -0.20))
        elif cmd == "a" and len(parts) >= 3:
            goto(float(parts[1]), float(parts[2]))
        elif cmd == "e":
            if len(parts) >= 2:
                goto(q1, float(parts[1]))    # absolute elbow, shoulder stays
            else:
                print(f"  elbow {q2:+.3f} rad ({q2 * 57.2958:+.0f} deg)")
        elif cmd in ("e+", "e-", "e++", "e--"):
            step = 0.05 if cmd in ("e+", "e-") else 0.20
            goto(q1, q2 + (step if cmd.endswith("+") else -step))
        elif cmd == "z":
            send("z")          # firmware: current pose becomes q = 0
            pump()
        elif cmd == "k":
            send("k")          # firmware: print the current centers
            pump()
        elif cmd == "m":
            label = " ".join(parts[1:]) or f"mark{len(marks) + 1}"
            marks.append((q1, q2, label))
            send(f"# MARK shoulder={q1:.3f} elbow={q2:.3f} {label}")
            print(f"  marked: shoulder {q1:+.3f} rad ({q1 * 57.2958:+.0f} deg)"
                  f" [{label}]")
        else:
            # one number = shoulder target; two numbers = shoulder + elbow
            goto(float(parts[0]),
                 float(parts[1]) if len(parts) > 1 else None)
    except ValueError:
        print("  ?  examples: 0.3   -1.2   a 0.3 -0.5   m neg_end   q")

print("\nmarked limits this session:")
for a, b, lab in marks:
    print(f"  shoulder {a:+.3f} rad ({a * 57.2958:+.0f} deg), elbow {b:+.3f}"
          f"  [{lab}]")
print("log: logs/shoulder_range_session.txt (send this file's marks over)")
log.close()
ser.close()
