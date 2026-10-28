---
title: 07 Parameters and References
description: SR-Support firmware parameters, the four reference sequences, verified status and licensing.
---

# 07 Parameters and References

## 7.1 Firmware parameters (`firmware/sr_support_b_ptk/include/config.h`)

| Parameter | Value | Meaning |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | 50 Hz control period |
| `MAX_CMD_RATE` | 0.08 rad/tick | Output slew limit (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Fall-gate up_z threshold |
| `FALL_W_QUIET` | 0.9 rad/s | Fall-gate angular-rate threshold |
| `FALL_CONFIRM_TICKS` | 25 | Fall-gate confirmation (0.5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Ticks per reference waypoint |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Retract rate |
| `EXEC_DONE_TICKS` | 50 | Consecutive standing ticks to finish |
| `EXEC_TIMEOUT_MS` | 14000 | Per-reference timeout |
| `EXEC_COOLDOWN_TICKS` | 75 | Cooldown after done/timeout (1.5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Pose-switch confirmation ticks |
| `EXEC_SWITCH_UP` | 0.60 | Max up_z for a switch |
| `EXEC_SWITCH_W` | 0.8 rad/s | Max angular rate for a switch |
| `EXEC_MIN_SWITCH_AGE` | 25 | Earliest tick for a switch |
| `EXEC_MAX_SWITCHES` | 5 | Max switches per run |
| `EXEC_NEUTRAL_MAX` | 120 | Max neutral-retract ticks |
| `SERVO_SHOULDER_CENTER_US` | 1840 | Shoulder zero pulse (re-indexed horn) |
| `SERVO_CENTER_US` | 1520 | Elbow zero pulse |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.07 / +2.07 rad | Shoulder travel |
| `Q_ELBOW_MIN/MAX` | ±0.80 rad | Manual/policy range (executor uses ±1.55 mechanically) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Servo direction |
| `IMU_YAW90` | 1 | IMU mounted 90° rotated |

## 7.2 Reference sequences (shoulder, elbow; rad)

| Pose | Sequence |
|---|---|
| `roll_pos` | `[2.0,-0.8] → [0,-0.8] → [0,0]` |
| `roll_neg` | `[2.0,-0.8] ×4 (hold) → [0,-0.8] → [0,0]` |
| `pitch_pos` | `[-1.07,1.55] → [0,1.55] → [0,0]` |
| `pitch_neg` | `[-1.07,-1.55] → [0,-1.55] → [0,0]` |

## 7.3 Verified status (2026-10-27)

- All four directions verified on the real robot: `pitch_neg` ~3 s, `pitch_pos` ~5–6 s,
  `roll_pos` ~3 s, `roll_neg` 5–14 s (roll over the top + pose re-plan);
- No servo envelope violations in any test;
- `roll_neg` is a hardware-specific sequence: the 1× simulation model differs in friction and
  arm mass (the real arm behaves like ~2× mass), so this direction does not reproduce in
  simulation. This is a known model gap, not a code mismatch.

## 7.4 Licensing

- B-line firmware/training code: MIT / Apache-2.0;
- B-line CAD/STL: CERN-OHL-S-2.0 (strong reciprocity — check obligations before commercial use);
- SelfRisingRobot: no license; this tutorial contains none of its code, waypoints or models;
- Patent CN109693729A/B: perform an FTO review before commercial use.
