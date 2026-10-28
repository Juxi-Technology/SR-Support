"""Put both servos back to the mechanical neutral (1520 us).

Sends the B-line firmware command ``r`` over serial: it re-arms the PWM
outputs and writes q = 0 on both joints (SERVO_CENTER_US = 1520 us), then
holds.  DTR/RTS are set before opening so the ESP32-S3 is not reset.

Run with the PlatformIO Python (pyserial is installed there):
  .venv-pio/Scripts/python.exe tools/servo_center.py --port COM27
"""

from __future__ import annotations

import argparse
import time

import serial


def main() -> None:
    p = argparse.ArgumentParser(description="Center both servos at 1520 us")
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
        print("OK: servos commanded to 1520 us neutral")
    elif "re-init failed" in text:
        print("FAIL: servo re-init failed; power/wiring, or power-cycle the board")


if __name__ == "__main__":
    main()
