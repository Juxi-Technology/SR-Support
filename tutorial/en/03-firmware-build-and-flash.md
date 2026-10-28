---
title: 03 Firmware Build and Flash
description: Build and flash the SR-Support B-line firmware with PlatformIO, serial commands and boot log.
---

# 03 Firmware Build and Flash

## 3.1 Environment

- **PlatformIO (Arduino framework)**, not ESP-IDF;
- Platform `espressif32 8.0.0`, Arduino core 3.3.12;
- Project: `firmware/sr_support_b_ptk/` (environment `ptk7452`);
- The repo ships a project-local PlatformIO: `.venv-pio/Scripts/pio.exe` (Windows).

## 3.2 Build and flash

```bash
# Build
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Close anything holding the serial port (serial monitor, `tools/hw_monitor.py`) before
> flashing, otherwise you get `could not open port` / `Access is denied`.

A successful build uses about RAM 7.3% and Flash 11.7%.

## 3.3 Serial monitor

```bash
.venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

Opening the port resets the ESP32. After reset you should see:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Serial commands (115200)

| Command | Function |
|---|---|
| `g` | Start/continue running (this build autoruns; usually not needed) |
| `s` | Stop the executor, hold the last target |
| `x` | Emergency release: detach PWM; re-arm with `r` |
| `r` | Re-initialize PWM and center |
| `t` | Servo self-test (small motion) |
| `c` | Recalibrate gyro bias (keep still) |
| `m <q1> <q2>` | Manual joint targets in rad |
| `1/2` | Manual shoulder ±0.5 rad |
| `3/4` | Manual elbow ±0.5 rad |
| `0` | Manual neutral |
| `l` | 3 s 50 Hz fast log |
| `k` | Print both servo center pulse widths |
| `o` / `p` | Shoulder center ±10 µs trim |
| `v` / `b` | Flip shoulder / elbow sign |
| `i` / `j` | Flip IMU X / Y sign |
| `h` | Stand-homing toggle (legacy policy path) |
| `a` | Legacy scripted get-up test mode |

## 3.5 Power-on behavior

The firmware defines `AUTORUN_ON_BOOT`: after power-up the executor waits for the robot to be
**fully down and still** for 0.5 s, then starts automatically — no `g` needed. Power up with
the robot upright.
