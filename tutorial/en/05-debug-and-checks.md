---
title: 05 Debug and checks
description: Telemetry format, IMU attitude checks and calibration, servo direction/center checks, four lying poses and the fall gate.
---

# 05 Debug and checks

## 5.1 Telemetry format

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

## 5.2 IMU checks and calibration

1. Keep the robot still and upright; confirm `up≈(0, 0, 1)` and `w≈0`;
2. Stand the robot LEVEL on a flat surface and keep it still; send `c` to calibrate gyro AND
   accel zero offsets together (`calibrating gyro+accel...`; the accel bias is stored in NVS
   and only counts when `accel bias ... (saved)` is printed; a `rejected` message means the
   robot was not level or not still - retry). **Factory units are already calibrated and
   stored in NVS** - only redo this after replacing/re-mounting the IMU, or when the lying
   check (step 5) shows a tilt problem;
3. Tilt slowly in x and y; the up components must respond in the correct direction without jumps;
4. If an axis is inverted, send `i` / `j` and recalibrate with `c`;
5. Lying check: after placing the robot and waiting 2 s, `up` must be stable and match the real
   pose (e.g. lying on the −Y side gives `up≈(0,−1,0)` with the base face flat). A persistent
   5°+ tilt while lying usually means the accel bias is uncalibrated - redo step 2.

## 5.3 Servo checks

| Check | Method | Expected |
|---|---|---|
| Centers | `k` | `centers: shoulder 1681 us, elbow 1456 us` (visual-center values baked 2026-11; re-zero per [page 06](./06-zero-tool)) |
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

## 5.4 Four lying poses and the fall gate

| Pose | Monitor `up` | Physical meaning |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | Body top points +X |
| `pitch_neg` | `(+1, 0, 0)` | Body top points −X |
| `roll_pos` | `(0, +1, 0)` | Body top points −Y |
| `roll_neg` | `(0, -1, 0)` | Body top points +Y |

Fall gate:

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Only then does the firmware print `getup start pose=...` and begin. Place the robot and
**release it, keeping it still for about 0.5 s**; flailing right after placement usually means
the hand is still touching it or the body is still rolling.

To verify: place the robot in each of the four poses above, release, and check that
`getup start pose=<matching pose>` appears within about 0.5 s.
