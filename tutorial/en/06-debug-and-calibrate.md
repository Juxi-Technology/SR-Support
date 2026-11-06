---
title: 06 Debug and calibration
description: Telemetry format, IMU and servo checks, gyro+accel calibration, center check, four lying poses and the fall gate, done criteria.
---

# 06 Debug and calibration

> **Finished-unit users can skip this page**: the factory calibrates and verifies every unit.
> Redo these steps only after replacing a servo/IMU, re-mounting a horn, or when a firmware
> upgrade is suspected to have disturbed the calibration.

This is the **whole-robot functional check and calibration** after assembly, flashing and
zeroing; work through it in order before using the robot.

> **Power while debugging**: USB carries serial data only. `c` needs just the IMU (the
> servos may stay unpowered); `t` / `z` / `e` need the 5 V servo rail on. If you do not want
> the ESP32 fed from two sources, unplug the 5 V branch to the ESP32, power it from USB alone
> and let the 5 V supply feed only the servos - a normal setup, see
> [page 04, section 4.4](./04-assembly).

## 6.1 Telemetry format

The firmware prints one telemetry line every 250 ms (the monitor summarizes it every 5 s):

```text
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Field | Meaning |
|---|---|
| `up` | World up vector in body coordinates (x forward, y left, z up) |
| `w` | Angular velocity (rad/s) |
| `q` | Current joint commands (shoulder, elbow, rad) |
| `qd` | Joint command rates |
| Mode | `run` / `hold` / `manual` / `auto` |

Quick hardware self-check (in the `SR-Support` folder with `.venv` activated):
`python tools/hw_check.py --port COM27` reads 0.6 s of telemetry; add `--tilt 8` and tilt the
robot by hand to print the up/gyro ranges and the tilt range, which reveals a stuck or
mis-oriented IMU.

## 6.2 IMU checks and calibration

1. First do the mechanical orientation check on [page 04, section 4.5](./04-assembly)
   (shoulder shaft toward IMU −Y, elbow shaft toward IMU +X), then keep the robot still and
   upright; confirm `up≈(0, 0, 1)` and `w≈0`;
2. Stand the robot LEVEL on a flat surface and keep it still; send `c` to calibrate gyro AND
   accel zero offsets together (`calibrating gyro+accel...`; the accel bias is stored in NVS
   and reloaded on boot). Success prints `accel bias ... (saved)`; `accel cal rejected` means
   the robot was not level or not still - retry. The factory has already done this per unit;
   redo it only after replacing/re-mounting the IMU or when the lying pose is off (step 5);
3. Tilt slowly left/right and forward/back; the x/y components of `up` must follow the real
   tilt with no jumps;
4. If the x or y direction is reversed, send `i` / `j` to flip the IMU axis signs, then `c`
   again;
5. Lying check: after placing the robot and waiting 2 s, `up` must be stable and match the real
   pose (e.g. lying on the −Y side gives `up≈(0,−1,0)` with the base face flat). A persistent
   5°+ tilt while lying usually means the accel bias is uncalibrated - redo step 2.

## 6.3 Servo checks and direction self-test

| Check | Method | Expected |
|---|---|---|
| Centers | `k` | `centers: shoulder 1681 us, elbow 1456 us` (visual-center values baked 2026-11; re-zero per [page 05](./05-zero-tool)) |
| Shoulder trim | `o` / `p` (±10 µs) | Arm vertical at `q=0` |
| Direction | `m 0.5 0` / `m 0 0.5` | Shoulder + → big arm toward −Y; elbow + → forearm toward +X |
| Sign flip | `v` (shoulder) / `b` (elbow) | Only if a direction is reversed |
| Self-test | `t` | Small motion on both joints, then center |
| Neutral | `m 0 0` or `r` | Arm vertical |

Joint limits:

- Shoulder manual commands `[-1.85, +1.82]` rad; elbow mechanical `±1.55` rad (reachable by the
  executor);
- Manual `m` commands clamp the elbow to `[-0.90, +0.70]` rad;
- PWM output 500–2500 µs at 50 Hz.

Send `t` and confirm: shoulder `q>0` → big arm toward **−Y**; elbow `q>0` → forearm toward
**+X**. Wrong direction: flip with `v` / `b`, or re-mount the horn.

## 6.4 Center check

Baked at the factory (shoulder 1681 µs / elbow 1456 µs) - **skippable for a stock unit**. In a
DIY build this was already done with the [page 05 zero-calibration](./05-zero-tool) and the
values baked into `config.h` (reflash if they changed); here just run `k` to confirm the
centers match the baked values. Return to page 05 only after re-indexing a horn, re-assembly,
or if the arm no longer rests at the visual center.

## 6.5 Four lying poses and the fall gate

| Pose | Monitor `up` | Physical meaning |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | Body top points toward +X |
| `pitch_neg` | `(+1, 0, 0)` | Body top points toward −X |
| `roll_pos` | `(0, +1, 0)` | Body top points toward −Y |
| `roll_neg` | `(0, -1, 0)` | Body top points toward +Y |

Fall-gate condition (firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Only then does it print `getup start pose=...` and begin. So place the robot, release it and
keep it still for ~0.5 s; waving it around right after placing usually means a hand is still
touching it or the body is still rolling.

Check: place the robot in each of the four poses, release and keep still; within 0.5 s the
serial log must show `getup start pose=<matching pose>`.

## 6.6 Done criteria

- [ ] `c` prints `accel bias ... (saved)`;
- [ ] `t` shows correct directions on both joints;
- [ ] `k` matches the baked centers (or you re-zeroed per page 05 and baked it);
- [ ] all four lying poses trigger `getup start`.
