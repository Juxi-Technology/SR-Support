"""Drive both servos to the firmware zero (arm vertical).

Sends the B-line firmware command ``r`` over serial: it re-arms the PWM
outputs and writes q = 0 on both joints at the baked centers (currently
shoulder 1681 us / elbow 1456 us), then holds.  For the 1520 us electrical
center used while installing the horns, flash the bench sketch
``firmware/servo_center_ptk`` instead.  DTR/RTS are set before opening so the
ESP32-S3 is not reset.

Run with the PlatformIO Python (pyserial is installed there):
  .venv-pio/Scripts/python.exe tools/servo_center.py --port COM27
"""

from __future__ import annotations

import argparse
import time

import serial


def main() -> None:
    p = argparse.ArgumentParser(description="Drive both servos to the firmware q=0 center")
    p.add_argument("--port", default="COM27")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--wait", type=float, default=2.0)
    args = p.parse_args()

    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = args.baud
    ser.timeout = 0.3
    ser.dtr = False
    ser.rts = False
    ser.open()
    time.sleep(0.2)
    ser.reset_input_buffer()
    ser.write(b"r")

    buf = b""
    t0 = time.time()
    while time.time() - t0 < args.wait:
        buf += ser.read(256)
    ser.close()

    text = buf.decode(errors="replace")
    print(text.encode("ascii", "replace").decode("ascii").strip()
          or "(no reply; check port/baud and that the firmware is running)")
    if "re-armed at neutral" in text:
        print("OK: servos commanded to the firmware q=0 center")
    elif "re-init failed" in text:
        print("FAIL: servo re-init failed; power/wiring, or power-cycle the board")


if __name__ == "__main__":
    main()
