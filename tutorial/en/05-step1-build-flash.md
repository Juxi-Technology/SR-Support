---
title: 05 Step 1: environment, build and flash
description: Build and flash the SR-Support B-line firmware with PlatformIO, serial commands and boot log.
---

# 05 Step 1: environment, build and flash

> **Finished-unit users can skip this page**: the factory has flashed and verified the
> firmware. Only redo this for firmware upgrades or after modifying the code.

## 5.1 Environment

- **PlatformIO (Arduino framework)**, not ESP-IDF;
- Platform `espressif32 8.0.0`, Arduino core 3.3.12;
- Project: `firmware/sr_support_b_ptk/` (environment `ptk7452`);
- The repo ships a project-local PlatformIO: `.venv-pio/Scripts/pio.exe` (Windows);
  install it first with `powershell -ExecutionPolicy Bypass -File tools/install_platformio.ps1`
  (needs Python 3.12 and the `py` launcher).

**Computer-side Python tools** (monitor, zeroing, twin) need pyserial/numpy/mujoco/gymnasium -
pick one of two options:

- Recommended: the project-local `.venv` (independent of PlatformIO's `.venv-pio`):
  `powershell -ExecutionPolicy Bypass -File tools/install_tools_env.ps1`;
- No virtual environment needed at all: in any Python 3.10+ install
  `pip install -r tools/requirements.txt` and replace `.venv\Scripts\python.exe` in the
  commands below with `python`.

> A virtual environment is not mandatory - it only isolates the dependencies from your system
> Python (MuJoCo is sensitive to versions, so it is recommended). The same holds for
> PlatformIO: the VS Code extension or a global `pio` works too; just replace
> `.venv-pio\Scripts\pio.exe` with the matching command.

## 5.2 Build and flash

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

## 5.3 Serial monitor

```bash
.venv-pio/Scripts/pio.exe device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

Opening the port resets the ESP32. After reset you should see:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 5.4 Serial commands (115200)

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
| `z` | Encoder-style zero: current pose becomes q=0 for both joints; prints the new pulses (RAM only; see [page 02](./02-zero-tool)) |
| `d` | Toggle the 50 Hz twin stream (MuJoCo twin; same switch on the status page) |
| `w` | Toggle WiFi (hotspot + status page/provisioning, see [page 08](./08-step4-wifi-twin)) |
| `v` / `b` | Flip shoulder / elbow sign |
| `i` / `j` | Flip IMU X / Y sign |
| `h` | Stand-homing toggle (legacy policy path) |
| `a` | Legacy scripted get-up test mode |

## 5.5 Power-on behavior

The firmware defines `AUTORUN_ON_BOOT`: after power-up the executor waits for the robot to be
**fully down and still** for 0.5 s, then starts automatically - no `g` needed. Power up with
the robot upright.
