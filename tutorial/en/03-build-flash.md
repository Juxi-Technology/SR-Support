---
title: 03 Flash the main firmware
description: Flash the SR-Support B-line firmware from the prebuilt bin (Flash Download Tool / esptool) or build it with PlatformIO; serial commands and boot log.
---

# 03 Flash the main firmware

> **Finished-unit users can skip this page**: the factory has flashed and verified the
> firmware. Only redo this for firmware upgrades or after modifying the code. Customers use
> the prebuilt image (3.1, no PlatformIO); developers build from source (3.2).

## 3.1 Flash the prebuilt image (recommended for customers)

1. Make sure you have `firmware/releases/sr_support_b_ptk_factory.bin` (checksums in
   `SHA256SUMS` next to it);
2. Enter download mode: hold **BOOT**, tap **RST**, release **BOOT**;
3. Flash it (tool setup on [page 02, section 2.4](./02-environment); run these commands in
   the `SR-Support` folder with `.venv` activated):
   - Windows GUI: Flash Download Tool → ESP32-S3 → load the bin at `0x0` → START;
   - Windows / Linux / macOS command line:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Press RST when done and read the log as in 3.3.

> Assembly centering needs no second image: after flashing this one, send `e` on the serial
> port and both servos output 1520 µs (see [page 04, section 4.2](./04-assembly)).

## 3.2 Build and flash from source (developers)

Environment: [page 02, section 2.5](./02-environment). Project:
`firmware/sr_support_b_ptk/` (environment `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Run these in the `SR-Support` folder with `.venv` activated (page 02, section 2.3). Close
> anything holding the serial port (serial monitor, `tools/hw_monitor.py`) before flashing,
> otherwise you get `could not open port` / `Access is denied`.

A successful build uses about RAM 56% and Flash 30% (WiFi + web server included; earlier
builds without WiFi were about 7% / 12%).

## 3.3 Serial monitor

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
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
| `c` | Calibrate gyro + **accel zero offsets** (robot must STAND LEVEL and still; stored in NVS) |
| `m <q1> <q2>` | Manual joint targets in rad |
| `1/2` | Manual shoulder ±0.5 rad |
| `3/4` | Manual elbow ±0.5 rad |
| `0` | Manual neutral |
| `l` | 3 s 50 Hz fast log |
| `k` | Print both servo center pulse widths |
| `o` / `p` | Shoulder center ±10 µs trim |
| `z` | Encoder-style zero: current pose becomes q=0 for both joints; prints the new pulses (RAM only; see [page 06](./06-zero-tool)) |
| `e` | Electrical center: both servos to 1520 µs (horn installation; independent of the baked zero; see [page 04, 4.2](./04-assembly)) |
| `d` | Toggle the 50 Hz twin stream (MuJoCo twin; same switch on the status page) |
| `w` | Toggle WiFi (hotspot + status page/provisioning, see [page 09](./09-wifi-twin)) |
| `v` / `b` | Flip shoulder / elbow sign |
| `i` / `j` | Flip IMU X / Y sign |
| `h` | Stand-homing toggle (legacy policy path) |
| `a` | Legacy scripted get-up test mode |

## 3.5 Power-on behavior

The firmware defines `AUTORUN_ON_BOOT`: after power-up the executor waits for the robot to be
**fully down and still** for 0.5 s, then starts automatically - no `g` needed. Power up with
the robot upright.
