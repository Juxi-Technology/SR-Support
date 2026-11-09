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
3. Flash it (tool setup on [page 02, section 2.4](./02-environment.md); run these commands in
   the `SR-Support` folder with `.venv` activated):
   - Windows GUI: Flash Download Tool → ESP32-S3 → load the bin at `0x0` → START;
   - Windows / Linux / macOS command line:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Press RST when done and read the log as in 3.3.

> For flashing / serial debugging you can power the ESP32 from USB and leave the 5 V supply
> to the servos only (the two power options are in [page 04, section 4.4](./04-assembly.md)).

> The command is **identical on Windows / Linux / macOS**; only the port changes:
> `COM27` on Windows, `/dev/ttyACM0` on Linux, `/dev/tty.usbmodem*` on macOS.
> Flash Download Tool is Windows-only; use the esptool command line elsewhere.

> Assembly centering needs no second image: after flashing this one, power up - both servos
> drive to the firmware zero (1681 / 1456 µs) - then power off and install the horns
> ([page 04, section 4.2](./04-assembly.md)). Optionally send `e` to put them at the 1520 µs
> electrical center first (equivalent).

## 3.2 Build and flash from source (developers)

Environment: [page 02, section 2.5](./02-environment.md). Project:
`firmware/sr_support_b_ptk/` (environment `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Run these in the `SR-Support` folder with `.venv` activated (page 02, section 2.3); they are
> identical on all three platforms - replace `COM27` in `--upload-port` with your port. Close
> anything holding the serial port (serial monitor, `tools/hw_monitor.py`) before flashing,
> otherwise you get `could not open port` / `Access is denied`.

A successful build uses about RAM 56% and Flash 30% (WiFi + web server included; earlier
builds without WiFi were about 7% / 12%).

## 3.3 Serial monitor

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Same on all three platforms; replace `COM27` with your port.)

> **Windows GUI serial assistant (optional)**: UartAssist from 野人家园 (free, single exe,
> Windows only). Official page <https://cmsoft.cn/resource/101.html>, official download
> entry <https://cmsoft.cn/resource/download/101>. Select the COM port, **115200, 8N1, no
> flow control**, enable "send newline"; watch the boot log/telemetry in the receive pane and
> type commands in the send box. Download it from the official link only (third-party sites
> often bundle adware); do not commit the exe to this repository.

**Linux / macOS serial viewers (pick one)**:

- Preferred: the `pio device monitor` command above (installed with the project, cross-platform);
- Lightweight CLI: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` on macOS; quit with `Ctrl-]`); the built-in
  `screen /dev/ttyACM0 115200` also works (quit with `Ctrl-A`, then `K`);
- GUI: **CoolTerm** (free, Windows/macOS/Linux, official site
  <https://freeware.the-meiers.org>); on Linux you can also `sudo apt install cutecom`.

> On Linux add your user to the `dialout` group: `sudo usermod -aG dialout $USER`, then log
> out and back in.

After opening the port, if the board was just powered or you pressed RST you will see the
boot log first; if not, press RST once. After reset you should see:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Serial commands (115200)

Type every command into the **send box** of the serial monitor/assistant and press Enter
(enable "send newline" in UartAssist); the `m` command needs a space and two values, e.g.
`m 0.5 0`.

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
| `z` | Encoder-style zero: current pose becomes q=0 for both joints; prints the new pulses (RAM only; see [page 05](./05-zero-tool.md)) |
| `e` | Electrical center (optional): both servos to 1520 µs for mounting the horns at the electrical center; the usual way is to power up to the firmware zero and mount there (see [page 04, 4.2](./04-assembly.md)) |
| `d` | Toggle the 50 Hz twin stream (MuJoCo twin; same switch on the status page) |
| `w` | Toggle WiFi (hotspot + status page/provisioning, see [page 08](./08-wifi.md)) |
| `v` / `b` | Flip shoulder / elbow sign |
| `i` / `j` | Flip IMU X / Y sign |
| `h` | Stand-homing toggle (legacy policy path) |
| `a` | Legacy scripted get-up test mode |

## 3.5 Power-on behavior

The firmware defines `AUTORUN_ON_BOOT`: after power-up the executor waits for the robot to be
**fully down and still** for 0.5 s, then starts automatically - no `g` needed. Power up with
the robot upright.

---

[← Back to the tutorial contents](./index.md)
