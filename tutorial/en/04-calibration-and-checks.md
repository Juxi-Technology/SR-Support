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
2. Send `c` to recalibrate the gyro bias (`calibrating gyro: keep still`);
3. Tilt slowly in x and y; the up components must respond in the correct direction without jumps;
4. If an axis is inverted, send `i` / `j` and recalibrate with `c`.

## 4.3 Servo checks

| Check | Method | Expected |
|---|---|---|
| Centers | `k` | `shoulder 1840 us, elbow 1520 us` (after re-index) |
| Shoulder trim | `o` / `p` (±10 µs) | Arm vertical at `q=0` |
| Direction | `m 0.5 0` / `m 0 0.8` | Shoulder + → big arm toward −Y; elbow + → forearm toward +X |
| Sign flip | `v` (shoulder) / `b` (elbow) | Only if a direction is reversed |
| Self-test | `t` | Small motion on both joints, then center |
| Neutral | `m 0 0` or `r` | Arm vertical |

Joint limits:

- Shoulder `[-1.07, +2.07]` rad; elbow mechanical `±1.55` rad;
- Manual `m` commands clamp the elbow to `±0.80` rad (policy range); the self-righting
  executor uses up to ±1.55 internally;
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
