---
title: SR-Support Self-Righting Robot Tutorial
description: Complete tutorial for the SR-Support 2-DOF self-righting device, from basics and assembly to firmware, calibration, self-righting usage and troubleshooting.
---

# SR-Support Self-Righting Robot Tutorial

SR-Support is a low-cost active self-righting device based on a 2-DOF arm. After tipping in
any direction it plants its two-joint arm on the ground, rolls and levers itself back upright.
This tutorial is organized as a reading order covering the full path from scratch to a
verified build.

## Reading order

| # | Page | Content | Note |
|---|---|---|---|
| 01 | [Basics](./01-basics) | Working principle, specs, BOM, tools, power safety | read first |
| 02 | [Zero-calibration tool](./02-zero-tool) | Arrow-key jog + `z` zeroing (after re-indexing/re-assembly) | tool page, skippable |
| 03 | [Debug and checks](./03-debug-and-checks) | Telemetry, IMU/servo checks, four lying poses, fall gate | debug page |
| 04 | [Assembly: print, build, wire](./04-assembly) | Printed parts, horn re-index, wiring table, IMU mounting | assembly tutorial |
| 05 | [Step 1: build and flash](./05-step1-build-flash) | PlatformIO build, flashing, serial commands, boot behavior | |
| 06 | [Step 2: calibration](./06-step2-calibrate) | Gyro+accel calibration, direction self-test, zeroing, fall-gate check | |
| 07 | [Step 3: self-righting usage](./07-step3-self-righting) | Four fall directions, expected motion, monitoring and logs | |
| 08 | [Step 4: WiFi and the twin](./08-step4-wifi-twin) | Status page, home-WiFi provisioning, wireless MuJoCo twin | optional |
| 09 | [Troubleshooting](./09-troubleshooting) | Common symptoms and fixes | reference |
| 10 | [Reference: model, parameters, licensing](./10-reference) | Model files (XML/STL), parameters, reference sequences, licensing | reference |

## Factory state of a finished unit (two reading paths)

This tutorial serves two audiences - pick the path that matches yours:

| Reader | Factory state | Recommended path |
|---|---|---|
| **Finished-unit user** | Assembled and wired, firmware flashed, **calibrated** (servo zeros and IMU accel zeros baked), **tested** (all four get-up directions verified per unit) | Go straight to [07 usage](./07-step3-self-righting) and [08 WiFi/twin](./08-step4-wifi-twin) (optional); keep [09](./09-troubleshooting)/[10](./10-reference) for reference. **Pages 04/05/06 are only needed for firmware upgrades, servo/IMU replacement or horn re-mounting** |
| **Kit / DIY builder** | Starts from parts | Follow [01](./01-basics) → [04](./04-assembly) → [05](./05-step1-build-flash) → [06](./06-step2-calibrate) → [07](./07-step3-self-righting) end to end |

> Recommended first-use check for a finished unit: power up upright → confirm `up≈(0,0,1)` →
> tip it once in each of the four directions per [page 07](./07-step3-self-righting) and
> confirm it stands up.

## Prerequisites

- Printed and assembled SR-Support mechanical parts (`footP`, `arm1P`, `arm2P`, `armhornP` ×2);
- ESP32-S3 board, Juxi ICM42670P IMU, passive direct-drive servo adapter board;
- 2× PTK7452MG (180° PWM) servos;
- A servo power supply (spec 6 V / ≥5 A) and a USB-C data cable;
- PlatformIO (recommended) or Arduino tooling on your computer.

## Verified status (2026-11-06)

All four fallen directions have been verified on the real robot, each as a **direct get-up**
(no roll-over needed), taking about 1–6 s; no servo envelope violations were recorded. The
kit also ships an arrow-key zero calibration tool ([page 02](./02-zero-tool)), a WiFi status
page with home-network provisioning, and a wireless MuJoCo live twin
([page 08](./08-step4-wifi-twin)).

## Safety

> - Hold the robot on first power-up, keep a 30 cm clear area, and send `x` or cut servo power
>   on any anomaly;
> - Never stall a servo longer than 1 s; stop when the case exceeds 60 °C;
> - 6 V goes to the servo rail only - **never** to the ESP32 5V/3V3;
> - Everything shares one ground; power-up order is in [page 04](./04-assembly).
