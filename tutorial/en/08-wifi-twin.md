---
title: 08 WiFi and the simulation twin
description: Status page, home-network provisioning, the wireless MuJoCo live twin and WiFi telemetry logging.
---

# 08 WiFi and the simulation twin

This step is optional and not required for self-righting itself.

## 8.1 Hotspot and status page

Hotspot: SSID `SR-Support`, password `srsupport`, address `192.168.4.1` (`w` toggles it; on by
default at boot). `w` is sent over serial: type `w` in the send box of the serial
monitor/assistant and press Enter; serial tools / the Windows UartAssist download are on
[page 03, section 3.3](./03-build-flash).

Join the hotspot and open `http://192.168.4.1` (phones usually pop the portal automatically).
The page refreshes every 300 ms: state, up vector and uprightness bar, joint commands, get-up
pose/phase, Home WiFi state and the twin-stream switch. If the browser uses a proxy, add an
exception for this address.

## 8.2 Provisioning (join the home WiFi)

On the status page use the Home WiFi card: `Scan` → pick a network → enter the password →
`Connect`. On success the ESP32 runs AP+STA:

- the hotspot stays up (bench work is unaffected);
- the robot is reachable on the home LAN (the page shows its `Robot IP`);
- credentials are stored in NVS and rejoined automatically on boot.

2.4 GHz only; scans/connects are refused while a get-up is running.

## 8.3 Wireless MuJoCo live twin

Press `Twin ON` on the status page (same as serial `d`), then:

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(In the `SR-Support` folder; create and activate `.venv` first as on
[page 02](./02-environment) - the tool environment is set up there too.)

- The window mirrors the real attitude live and keeps the body on the floor;
- The arm is held at its floor-contact angle like the stalled servo (no floor penetration);
- The USB cable is only needed for flashing and log dumps;
- Replay a recorded log offline with `--replay <file>`.

## 8.4 WiFi telemetry logging

```bash
python tools/tcp_log.py
```

Saves the hotspot telemetry stream to `logs/wifi_<time>.txt` for offline replay and analysis.

## 8.5 Simulation and training reference

The repo ships the MuJoCo model and training code (`training/b_line/`) for replay and
retraining; the model files are described on [page 10](./10-reference).
