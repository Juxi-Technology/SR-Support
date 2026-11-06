---
title: 04 Calibration and Checks
description: IMU attitude, servo direction and center, joint limits and fall-gate checks for SR-Support.
---

# 04 Calibration and Checks

## 4.1 Telemetry format

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

## 4.2 IMU checks

1. Keep the robot still and upright; confirm `up≈(0, 0, 1)` and `w≈0`;
2. Stand the robot LEVEL on a flat surface and keep it still; send `c` to calibrate gyro AND
   accel zero offsets together (`calibrating gyro+accel...`; the accel bias is stored in NVS
   and only counts when `accel bias ... (saved)` is printed; a `rejected` message means the
   robot was not level or not still - retry);
3. Tilt slowly in x and y; the up components must respond in the correct direction without jumps;
4. If an axis is inverted, send `i` / `j` and recalibrate with `c`;
5. Lying check: after placing the robot and waiting 2 s, `up` must be stable and match the real
   pose (e.g. lying on the −Y side gives `up≈(0,−1,0)` with the base face flat). A persistent
   5°+ tilt while lying usually means the accel bias is uncalibrated - redo step 2.

## 4.3 Servo checks

| Check | Method | Expected |
|---|---|---|
| Centers | `k` | `shoulder 1681 us, elbow 1456 us` (visual-center values baked 2026-11; re-zero per 4.5) |
| Shoulder trim | `o` / `p` (±10 µs) | Arm vertical at `q=0` |
| Direction | `m 0.5 0` / `m 0 0.8` | Shoulder + → big arm toward −Y; elbow + → forearm toward +X |
| Sign flip | `v` (shoulder) / `b` (elbow) | Only if a direction is reversed |
| Self-test | `t` | Small motion on both joints, then center |
| Neutral | `m 0 0` or `r` | Arm vertical |

Joint limits:

- Shoulder manual commands `[-1.85, +1.82]` rad; elbow mechanical `±1.55` rad (reachable by the
  executor);
- Manual `m` commands clamp the elbow to `[-0.90, +0.70]` rad;
- PWM output 500–2500 µs at 50 Hz.

## 4.4 Four lying poses and the fall gate

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

## 4.5 Centers / zero calibration (arrow-key tool + `z`)

The firmware defines q=0 as the visual center: arm vertical, both links in one line. After
re-indexing a horn, swapping a servo or re-assembling, re-zero as follows:

1. Connect both the battery and USB (servos powered) and run:

   ```bash
   .venv/Scripts/python.exe tools/hw_shoulder_range.py
   ```

   A persistent three-line display updates in place: `↑`/`↓` = big arm ±0.05 rad,
   `←`/`→` = small arm ±0.05 rad (Shift = ±0.20); `z` = set the current pose as the center;
   `k` = read the centers; `n` = neutral; `q` = quit.

2. Jog until the arm looks vertical and aligned, press `z`; the firmware prints:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

3. Write the two pulse values back into `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`), shift every waypoint of `EXEC_REF*` and
   `training/b_line/getup_reference_b39.py` by the same offsets (shoulder/elbow each −Δ rad),
   and reflash;
4. Re-test all four directions.

> `z` only touches RAM; a reboot restores the old zero. Once satisfied, step 3 is mandatory,
> otherwise the physical get-up poses drift. A mis-press is harmless: zero again to overwrite.
