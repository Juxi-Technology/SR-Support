---
title: 01 Basics
description: SR-Support working principle, specifications and BOM.
---

# 01 Basics

## 1.1 Working principle

SR-Support is a 2-DOF (shoulder + elbow) active self-righting device:

- **Mechanism**: a two-joint arm mounted on a square base; the shoulder swings about the body's
  long axis and the elbow folds the forearm;
- **Sensing**: a 6-axis IMU provides the attitude quaternion; the firmware classifies each fall
  into one of four poses (`pitch_pos/neg`, `roll_pos/neg`, see
  [page 06](./06-debug-and-calibrate) 6.5) from the body-frame up vector;
- **Actuation**: a reference-sequence executor - each pose has a waypoint schedule
  (20 ticks per waypoint, 0.08 rad/tick slew) that plants/levers the arm to roll the body back
  upright; `roll_neg` additionally uses elbow-wedge pumps and a whip-slam fallback;
- **Fallbacks**: 14 s timeout, pose re-planning and automatic retry after the fall gate;
  `roll_neg` uses per-stage adaptive holds and exits to retract as soon as it is upright;
- **Verified**: four directions stand up directly in about 1-6 s; the same model drives the
  MuJoCo simulation and the live hardware twin ([page 08](./08-wifi-twin)).

## 1.2 Overview

| Item | Specification |
|---|---|
| Base | ~88 × 82 mm shell, 68 mm tall (bottom plate + shell + shoulder mount, 3D printed) |
| Arm | Shoulder axis 56 mm above the base, elbow 40.1 mm above the shoulder; forearm strut ~17 cm (12 mm tube) |
| Mass | ~133 g (model mass table: foot 92.1 / arm1 20.7 / arm2 20.1 g, including both servos) |
| Shoulder | PTK7452MG; manual limits `[-1.85, +1.82]` rad (sim joint range `[-1.07, +2.07]`) |
| Elbow | PTK7452MG; manual limits `[-0.90, +0.70]` rad (mechanical ~±1.55 rad) |
| Controller | ESP32-S3-DevKitC-1 (Arduino framework / PlatformIO) |
| Attitude | Juxi ICM42670P 6-axis IMU (I²C address 0x23, 100 kHz) |
| Servo drive | ESP32 LEDC, 50 Hz, 14 bit, 500–2500 µs pulse width |

## 1.3 BOM

| Category | Part | Qty | Notes |
|---|---|---|---|
| Structure | 3D printed: bottom plate, shoulder servo mount, elbow servo mount, top strut | 1 each | PETG or PLA, 15% infill; servo horns are the ones bundled with the servos |
| Actuation | PTK7452MG 180° PWM servo | 2 | Metal gear, 25T, ~12.2 g, ~3.4 kg·cm at 6 V |
| Controller | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Sensor | Juxi ICM42670P IMU module | 1 | 3.3 V supply |
| Adapter | Passive servo adapter board | 1 | GPIO → 3-pin headers, shared V+/GND, no PCA9685 |
| Wiring | USB-C data cable, Dupont wires, servo extensions | several | — |
| Power | Servo supply 5 V / ≥5 A | 1 | Separate from the ESP32, common ground; **verified for all four get-up directions** |
