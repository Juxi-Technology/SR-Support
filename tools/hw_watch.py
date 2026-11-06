"""Live fixed-line serial dashboard for SR-Support (B line).

Instead of scrolling one line every 250 ms like ``pio device monitor``, this
redraws a small block in place (up vector/tilt, gyro, joint commands, mode,
last event) and forwards commands typed at the ``cmd>`` prompt to the
firmware. Events are appended to ``logs/hw_watch.log``.

Run (project .venv activated, from the SR-Support folder):
  python tools/hw_watch.py --port COM27

Type a command and press Enter (e.g. c, t, k, m 0.5 0). Ctrl-C quits.
Opening the port does not reset the board (DTR/RTS are held low).
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import serial

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "hw_watch.log"

TELEM = re.compile(
    r"up\s+(\S+)\s+(\S+)\s+(\S+).*w\s+(\S+)\s+(\S+)\s+(\S+)"
    r".*q\s+(\S+)\s+(\S+).*\|\s+(\w+)")
EVENT_KEYS = ("armed", "disarmed", "pump", "push", "stand", "fall", "IMU",
              "roll-up", "getup", "executor", "calibrat", "zero set",
              "manual", "timeout", "re-plan")

N_LINES = 6


class State:
    def __init__(self) -> None:
        self.up = (0.0, 0.0, 1.0)
        self.w = (0.0, 0.0, 0.0)
        self.q = (0.0, 0.0)
        self.mode = "?"
        self.event = ""
        self.cmd = ""


def reader(ser: serial.Serial, st: State, stop: threading.Event) -> None:
    buf = ""
    while not stop.is_set():
        try:
            data = ser.read(256)
        except Exception:
            break
        if not data:
            continue
        buf += data.decode("utf-8", "replace")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            m = TELEM.search(line)
            if m:
                st.up = tuple(float(m.group(i)) for i in (1, 2, 3))
                st.w = tuple(float(m.group(i)) for i in (4, 5, 6))
                st.q = (float(m.group(7)), float(m.group(8)))
                st.mode = m.group(9)
                continue
            if any(k in line for k in EVENT_KEYS):
                st.event = f"{datetime.now():%H:%M:%S} {line}"
                try:
                    LOG.parent.mkdir(parents=True, exist_ok=True)
                    with LOG.open("a", encoding="utf-8") as f:
                        f.write(st.event + "\n")
                except OSError:
                    pass


class Keys:
    def __init__(self) -> None:
        self.win = sys.platform.startswith("win")
        if self.win:
            import msvcrt
            self.msvcrt = msvcrt
            os.system("")  # enable ANSI escape handling in conhost
        else:
            import select
            import termios
            import tty
            self.select = select
            self.termios = termios
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)

    def get(self) -> str | None:
        if self.win:
            if self.msvcrt.kbhit():
                return self.msvcrt.getwch()
            return None
        r, _, _ = self.select.select([sys.stdin], [], [], 0)
        return sys.stdin.read(1) if r else None

    def close(self) -> None:
        if not self.win:
            self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.old)


def render(lines: list[str], move_up: int) -> None:
    out = f"\x1b[{move_up}A" if move_up else ""
    for ln in lines:
        out += "\x1b[2K" + ln + "\n"
    sys.stdout.write(out)
    sys.stdout.flush()


def make_lines(st: State, port: str) -> list[str]:
    ux, uy, uz = st.up
    wx, wy, wz = st.w
    q1, q2 = st.q
    uz_c = max(-1.0, min(1.0, uz))
    tilt = math.degrees(math.acos(uz_c))
    wn = math.sqrt(wx * wx + wy * wy + wz * wz)
    event = (st.event[:40] if st.event else "-")
    cmd = st.cmd[-36:]
    lines = [
        f"SR-Support {port}  (Ctrl-C quit)",
        f"up  x{ux:+.2f} y{uy:+.2f} z{uz:+.2f} tilt {tilt:4.1f}",
        f"w   {wx:+.1f} {wy:+.1f} {wz:+.1f} rad/s |w| {wn:.1f}",
        f"q   sh {q1:+.2f} el {q2:+.2f} mode {st.mode}",
        f"event {event}",
        f"cmd> {cmd}",
    ]
    width = max(20, shutil.get_terminal_size().columns - 1)
    return [ln[:width] for ln in lines]


def main() -> int:
    ap = argparse.ArgumentParser(description="Live fixed-line SR-Support dashboard")
    ap.add_argument("--port", default="COM27", help="serial port, e.g. COM27")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = args.baud
    ser.timeout = 0.2
    ser.dtr = False
    ser.rts = False
    ser.open()

    st = State()
    stop = threading.Event()
    th = threading.Thread(target=reader, args=(ser, st, stop), daemon=True)
    th.start()
    keys = Keys()

    print("live: type at cmd>, Ctrl-C quits")
    move_up = 0
    try:
        while True:
            ch = keys.get()
            if ch:
                if ch == "\x03":  # Ctrl-C
                    break
                if ch in ("\r", "\n"):
                    cmd = st.cmd.strip()
                    st.cmd = ""
                    if cmd:
                        ser.write((cmd + "\n").encode())
                elif ch in ("\x08", "\x7f"):
                    st.cmd = st.cmd[:-1]
                elif ch.isprintable():
                    st.cmd += ch
            render(make_lines(st, args.port), move_up)
            move_up = N_LINES
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        th.join(timeout=0.5)
        try:
            ser.close()
        except Exception:
            pass
        keys.close()
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
