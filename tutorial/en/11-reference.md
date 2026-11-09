---
title: 11 Reference: model, parameters and licensing
description: Reference model files (MuJoCo XML / STL), firmware parameters, the four reference sequences, verified status and licensing.
---

# 11 Reference: model, parameters and licensing

## 11.1 Reference model files

The simulation uses MuJoCo MJCF (`.xml` + `.stl` meshes), sharing the hardware's own design:

| File | Description |
|---|---|
| `hardware/v1/robot_v1.xml` | Main model (geometry/mass matched to the hardware) |
| `hardware/v1/meshes/*.stl` | 6 STL meshes that assemble into 4 printed groups (base plate/shell, shoulder mount, upper-arm bracket/elbow mount, forearm) |
| `hardware/v1/meshes/print_mass_model.json` | Per-part printed mass table (15% infill) |

No URDF is bundled; for ROS use, export one from the CAD/meshes above.

## 11.2 Firmware parameters (`firmware/sr_support_b_ptk/include/config.h`)

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
| `SERVO_SHOULDER_CENTER_US` | 1681 | Shoulder zero pulse (visual-center value baked 2026-11; re-zero per [page 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Elbow zero pulse (same) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Shoulder manual-command limits |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Manual range (executor uses ±1.55 mechanically) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Servo direction |
| `IMU_YAW90` | 1 | IMU mounted 90° rotated |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Attitude filter: accel-correction gain / trust band |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Hotspot (`w` toggles it; on at boot) |

## 11.3 Reference sequences (shoulder, elbow; rad; value-for-value with `training/b_line/getup_reference_b39.py`)

| Pose | Sequence |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` full-speed direct press (hold ≤40 ticks) → wedge pumps `[-1.80,0.35] → [-1.80,0.05]` ×2 (each hold ≤30) → fallback: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (whip-slam, hold ≤40) → final hold ≤90 → retract |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 11.4 Verified status and factory inspection (2026-11-06)

- **Factory inspection**: each finished unit gets - servo zeros defined and baked per unit
  ([page 05](./05-zero-tool.md)), gyro + accel zero calibration (NVS), and a four-direction
  get-up test before shipping;
- All four directions verified on the real robot, each as a **direct get-up** (no roll-over),
  about 1–6 s; no servo envelope violations;
- `roll_neg` final recipe: full-travel direct press + elbow-wedge pumps ×2, whip-slam retry as
  fallback (the earlier roll-over + re-plan scheme is retired);
- The attitude pipeline was corrected with accel-bias calibration (see
  [page 06, 6.2](./06-debug-and-calibrate.md)); lying poses now match the real robot;
- `roll_neg` still does not reproduce in the 1× mass simulation model (arm mass/friction
  differ); that is a known model gap - the hardware firmware is validated on hardware.

## 11.5 Licensing

- B-line firmware/training code: MIT / Apache-2.0;
- B-line CAD/STL: CERN-OHL-S-2.0 (strong reciprocity — check obligations before commercial use);
- SelfRisingRobot: no license; this tutorial contains none of its code, waypoints or models;
- Patent CN109693729A/B: perform an FTO review before commercial use.

---

[← Back to the tutorial contents](./index.md)
