"""Interactive arm zeroing / travel tool (live robot, arrow keys).

The operator drives the arm with the arrow keys and watches it; this tool
sends the commands and records the session. Run it in a terminal with the
servo battery and the USB cable both connected:

    .venv/Scripts/python.exe tools/hw_shoulder_range.py

Arrow keys:
    up / down       big arm (shoulder)  +-0.05 rad   (Shift: +-0.20)
    left / right    small arm (elbow)   -+0.05 rad   (Shift: +-0.20)

Single keys:
    z               firmware zero: the CURRENT pose becomes q = 0
                    (both joints; prints the new PWM centers in us)
    k               print the firmware PWM centers
    n               neutral (0, 0)
    m               mark the current pose in the session log
    q               quit (goes to neutral first)

On terminals without raw-key support the tool falls back to typed
commands (numbers, e 0.1, z, k, n, m, q).

Everything lands in logs/shoulder_range_session.txt. There is no servo
position feedback: the centers printed by `z` are baked into config.h
(SERVO_SHOULDER_CENTER_US / SERVO_CENTER_US) and every get-up waypoint
is shifted by the same offset so the physical poses stay identical.
Manual-mode software limits mirror config.h (Q_SHOULDER_MIN/MAX).
"""
from __future__ import annotations

import time
from datetime import datetime

import serial

try:
    import msvcrt                     # Windows raw console keys
    HAVE_ARROWS = True
except ImportError:
    HAVE_ARROWS = False

PORT = "COM27"
BAUD = 115200
Q_MIN, Q_MAX = -1.85, 1.82       # config.h manual clamp
STEP = 0.05
BIG = 0.20
MOVE_GAP = 0.15                  # s between accepted moves (key repeat)

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


def pump(sec: float = 0.5) -> None:
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
marks: list[tuple[float, float]] = []


def goto(a: float | None = None, b: float | None = None) -> None:
    global q1, q2
    if a is not None:
        q1 = max(Q_MIN, min(Q_MAX, float(a)))
    if b is not None:
        q2 = float(b)
    send(f"m {q1:.3f} {q2:.3f}")
    pump()
    print(f"  shoulder {q1:+.3f} ({q1 * 57.2958:+.0f} deg)  "
          f"elbow {q2:+.3f} ({q2 * 57.2958:+.0f} deg) | {latest_up}")


def do_zero() -> None:
    send("z")
    pump()


def do_mark() -> None:
    marks.append((q1, q2))
    send(f"# MARK shoulder={q1:.3f} elbow={q2:.3f}")
    print(f"  marked: shoulder {q1:+.3f}, elbow {q2:+.3f}")


send("m 0.000 0.000")
pump()
print("connected. shoulder +0.000, elbow +0.000.")
if HAVE_ARROWS:
    print("up/down = big arm +-0.05, left/right = small arm -+0.05,")
    print("Shift = +-0.20;  z = set zero here,  k = read centers,")
    print("n = neutral,  m = mark,  q = quit")
else:
    print("arrow keys unsupported here; type numbers / z / k / n / m / q")

last_move = 0.0


def key_loop() -> None:
    global last_move
    while True:
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):          # extended key: arrows etc.
            ext = msvcrt.getch()
            now = time.time()
            if now - last_move < MOVE_GAP:
                continue                       # swallow OS key repeat
            if ext in (b"H", b"Q"):            # up / Shift+up
                goto(q1 + (BIG if ext == b"Q" else STEP))
            elif ext in (b"P", b"R"):          # down / Shift+down
                goto(q1 - (BIG if ext == b"R" else STEP))
            elif ext in (b"K", b"S"):          # left / Shift+left
                goto(None, q2 - (BIG if ext == b"S" else STEP))
            elif ext in (b"M", b"T"):          # right / Shift+right
                goto(None, q2 + (BIG if ext == b"T" else STEP))
            last_move = now
            continue
        c = ch.decode(errors="replace").lower()
        if c == "q":
            return
        if c == "z":
            do_zero()
        elif c == "k":
            send("k")
            pump()
        elif c == "n":
            goto(0.0, 0.0)
        elif c == "m":
            do_mark()


def line_loop() -> None:
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not line:
            continue
        parts = line.replace(",", " ").split()
        cmd = parts[0].lower()
        try:
            if cmd in ("q", "quit", "exit"):
                return
            if cmd in ("n", "0"):
                goto(0.0, 0.0)
            elif cmd in ("+", "-"):
                goto(q1 + (STEP if cmd == "+" else -STEP))
            elif cmd in ("++", "--"):
                goto(q1 + (BIG if cmd == "++" else -BIG))
            elif cmd == "a" and len(parts) >= 3:
                goto(float(parts[1]), float(parts[2]))
            elif cmd == "e":
                if len(parts) >= 2:
                    goto(None, float(parts[1]))
                else:
                    print(f"  elbow {q2:+.3f} rad")
            elif cmd == "z":
                do_zero()
            elif cmd == "k":
                send("k")
                pump()
            elif cmd == "m":
                do_mark()
            else:
                goto(float(parts[0]),
                     float(parts[1]) if len(parts) > 1 else None)
        except ValueError:
            print("  ?  examples: 0.3   -1.2   0.3 -0.5   z   q")


try:
    if HAVE_ARROWS:
        key_loop()
    else:
        line_loop()
except KeyboardInterrupt:
    pass
goto(0.0, 0.0)
print("\nmarked poses this session:")
for a, b in marks:
    print(f"  shoulder {a:+.3f} rad, elbow {b:+.3f} rad")
print("log: logs/shoulder_range_session.txt")
log.close()
ser.close()
