---
title: 04 Step 1: build and flash
description: Build and flash the SR-Support B-line firmware with PlatformIO, serial commands and boot log.
---

# 04 Step 1: build and flash

> **Finished-unit users can skip this page**: the factory has flashed and verified the
> firmware. Only redo this for firmware upgrades or after modifying the code.

The environment (PlatformIO and the computer-side tools) is installed on [page 02](./02-environment); this page builds and flashes.

## 4.1 Build and flash

```bash
# Build
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
.venv-pio/Scripts/pio.exe run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Close anything holding the serial port (serial monitor, `tools/hw_monitor.py`) before
> flashing, otherwise you get `could not open port` / `Access is denied`.

A successful build uses about RAM 56% and Flash 30% (WiFi + web server included; earlier
builds without WiFi were about 7% / 12%).

## 4.2 Serial monitor

```bash
.venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

Opening the port resets the ESP32. After reset you should see:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 4.3 Serial commands (115200)

| Command | Function |
|---|---|
| `g` | Start/continue running (this build autoruns; usually not needed) |
| `s` | Stop the executor, hold the last target |
| `x` | Emergency release: detach PWM; re-arm with `r` |
| `r` | Re-initialize PWM and center |
| `t` | Servo self-test (small motion) |
| `c` | Calibrate gyro + **accel zero offsets** (robot must STAND LEVEL and still; stored in NVS) |
| `m <q1> <q2>` | Manual joint targets in rad |
| `1/2` | Manual shoulder ±0.5 rad |
| `3/4` | Manual elbow ±0.5 rad |
| `0` | Manual neutral |
| `l` | 3 s 50 Hz fast log |
| `k` | Print both servo center pulse widths |
| `o` / `p` | Shoulder center ±10 µs trim |
| `z` | Encoder-style zero: current pose becomes q=0 for both joints; prints the new pulses (RAM only; see [page 06](./06-zero-tool)) |
| `d` | Toggle the 50 Hz twin stream (MuJoCo twin; same switch on the status page) |
| `w` | Toggle WiFi (hotspot + status page/provisioning, see [page 09](./09-wifi-twin)) |
| `v` / `b` | Flip shoulder / elbow sign |
| `i` / `j` | Flip IMU X / Y sign |
| `h` | Stand-homing toggle (legacy policy path) |
| `a` | Legacy scripted get-up test mode |

## 4.4 Power-on behavior

The firmware defines `AUTORUN_ON_BOOT`: after power-up the executor waits for the robot to be
**fully down and still** for 0.5 s, then starts automatically - no `g` needed. Power up with
the robot upright.
