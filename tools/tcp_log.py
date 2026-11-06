"""Save the robot's WiFi telemetry stream to a file.

The firmware opens a WiFi AP (SSID 'SR-Support', password 'srsupport') and
streams the 50 Hz state lines on TCP port 3333. Join that network, then:

  python tools/tcp_log.py                # writes logs/wifi_telemetry.txt
  python tools/tcp_log.py 192.168.4.1 3333 logs/my_test.txt

Ctrl-C stops the capture; every line is flushed so the file is safe if the
robot resets.
"""

from __future__ import annotations

import socket
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.4.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 3333
    out = (Path(sys.argv[3]) if len(sys.argv) > 3
           else ROOT / "logs" / f"wifi_{datetime.now():%H%M%S}.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    sock = socket.create_connection((host, port), timeout=5.0)
    sock.settimeout(0.5)
    print(f"connected {host}:{port} -> {out} (Ctrl-C to stop)", flush=True)
    t0 = time.time()
    n = 0
    buf = ""
    with out.open("w", encoding="utf-8") as f:
        try:
            while True:
                try:
                    data = sock.recv(4096)
                except socket.timeout:
                    continue
                if not data:
                    print("connection closed by the robot", flush=True)
                    break
                buf += data.decode("utf-8", "replace")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line:
                        f.write(f"{time.time() - t0:8.3f} {line}\n")
                f.flush()
                n += 1
        except KeyboardInterrupt:
            pass
    sock.close()
    size = out.stat().st_size
    print(f"saved {size} bytes -> {out}", flush=True)


if __name__ == "__main__":
    main()
