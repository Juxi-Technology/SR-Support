---
title: 01 Basics
description: SR-Support working principle, specifications, BOM, tools and power safety.
---

# 01 Basics

## 1.1 Working principle

SR-Support is a 2-DOF (shoulder + elbow) active self-righting device:

- **Mechanism**: a two-joint arm mounted on a square base; the shoulder swings about the body's
  long axis and the elbow folds the forearm;
- **Sensing**: a 6-axis IMU provides the attitude quaternion; the firmware classifies each fall
  into one of four poses (`pitch_pos/neg`, `roll_pos/neg`, see
  [page 03](./03-debug-and-checks) 3.4) from the body-frame up vector;
- **Actuation**: a reference-sequence executor - each pose has a waypoint schedule
  (20 ticks per waypoint, 0.08 rad/tick slew) that plants/levers the arm to roll the body back
  upright; `roll_neg` additionally uses elbow-wedge pumps and a whip-slam fallback;
- **Fallbacks**: 14 s timeout, pose re-planning and automatic retry after the fall gate;
  `roll_neg` uses per-stage adaptive holds and exits to retract as soon as it is upright;
- **Verified**: four directions stand up directly in about 1-6 s; the same model drives the
  MuJoCo simulation and the live hardware twin ([page 08](./08-step4-wifi-twin)).

## 1.2 Overview

| Item | Specification |
|---|---|
| Base | 8.5 × 8.5 cm square; total height 4 cm (37 mm riser + 3 mm foot plate) |
| Arm | About 26 cm tall when upright (upper arm + forearm) |
| Mass | About 102 g with both servos and electronics (to be calibrated by weighing) |
| Shoulder | PTK7452MG; manual limits `[-1.85, +1.82]` rad in the visual-zero frame |
| Elbow | PTK7452MG, usable travel about ±1.55 rad |
| Controller | ESP32-S3-DevKitC-1 (Arduino framework / PlatformIO) |
| Attitude | Juxi ICM42670P 6-axis IMU (I²C address 0x23, 100 kHz) |
| Servo drive | ESP32 LEDC, 50 Hz, 14 bit, 500–2500 µs pulse width |

## 1.3 BOM

| Category | Part | Qty | Notes |
|---|---|---|---|
| Structure | 3D printed `footP` / `arm1P` / `arm2P` / `armhornP` | 1 / 1 / 1 / 2 | PETG or PLA; weigh after printing |
| Actuation | PTK7452MG 180° PWM servo | 2 | Metal gear, 25T, ~12.2 g, ~3.4 kg·cm at 6 V |
| Controller | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Adapter | Passive servo adapter board | 1 | GPIO → 3-pin headers, shared V+/GND, no PCA9685 |
| Sensor | Juxi ICM42670P IMU module | 1 | 3.3 V supply |
| Power | Servo supply 6 V / ≥5 A | 1 | Separate from the ESP32 (5 V also works, see 1.5) |
| Power | Electrolytic 1000–2200 µF + 100 nF | 1 each | At the servo supply terminals |
| Power | 5 A fuse / resettable fuse + switch | 1 set | — |
| Wiring | USB-C data cable, Dupont wires, servo extensions | several | — |
| Fasteners | M2/M3 screws, zip ties, rubber O-rings | several | O-rings for tip grip |

## 1.4 Tools

- Calipers and a multimeter (continuity/voltage);
- Screwdrivers and hex keys;
- A computer with PlatformIO (recommended) or Arduino IDE;
- Optional: servo tester, INA219 current monitor.

## 1.5 Power and safety

- The 2× PTK7452MG are specified for a **6 V / ≥5 A** supply; 7.4 V reaches ~4.5 kg·cm but heat
  and current must be measured;
- **5 V works** (the reference build runs at 5 V): stall torque drops ~15% and `roll_neg` leans
  more on the wedge pumps; use 6 V for extra margin;
- Add 1000–2200 µF plus 100 nF at the servo supply, a 5 A fuse and a power switch;
- Power the ESP32 separately from USB-C 5 V and tie the grounds together;
- **Never connect 6 V/7.4 V to the ESP32 5V/3V3**, and never drive both servos from a PC USB port;
- Power-up order: ground and signals first → servos → ESP32. Reverse when powering down.
