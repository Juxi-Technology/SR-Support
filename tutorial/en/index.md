---
title: SR-Support Self-Righting Robot Tutorial
description: Complete tutorial for the SR-Support 2-DOF self-righting device, from basics and environment setup to assembly, firmware, calibration, self-righting usage and troubleshooting.
---

# SR-Support Self-Righting Robot Tutorial

SR-Support is a low-cost active self-righting device based on a 2-DOF arm. After tipping in
any direction it plants its two-joint arm on the ground, rolls and levers itself back upright.
This tutorial is organized as a reading order covering the full path from scratch to a
verified build.

## Reading order

| # | Page | Content | Note |
|---|---|---|---|
| 01 | [Basics](./01-basics) | Working principle, specs, BOM | read first |
| 02 | [Environment setup](./02-environment) | Create/activate `.venv`, prebuilt firmware + flash tools (Flash Download Tool / esptool), computer-side tools and MuJoCo env, optional PlatformIO, serial port | **do this first** |
| 03 | [Flash the main firmware](./03-build-flash) | Prebuilt bin (recommended for customers) or a PlatformIO source build, serial commands, boot behavior | skippable for stock units |
| 04 | [Assembly: print, build, wire](./04-assembly) | Printed parts, horn index, wiring table, IMU mounting | skippable for stock units |
| 05 | [Debug and checks](./05-debug-and-checks) | Telemetry, IMU/servo checks, four lying poses, fall gate | debug page |
| 06 | [Zero-calibration](./06-zero-tool) | Arrow-key jog + `z` zeroing (after re-indexing/re-assembly) | **required for DIY builds**; skippable for stock units |
| 07 | [Calibration](./07-calibrate) | Gyro+accel calibration, direction self-test, zero check, fall-gate check | |
| 08 | [Self-righting usage and monitoring](./08-self-righting) | Four fall directions, expected motion, monitoring and logs | |
| 09 | [WiFi and the simulation twin](./09-wifi-twin) | Status page, home-WiFi provisioning, wireless MuJoCo twin | optional |
| 10 | [Troubleshooting](./10-troubleshooting) | Common symptoms and fixes | reference |
| 11 | [Reference: model, parameters, licensing](./11-reference) | Model files (XML/STL), parameters, reference sequences, licensing | reference |

## Factory state of a finished unit (two reading paths)

This tutorial serves two audiences - pick the path that matches yours:

| Reader | Factory state | Recommended path |
|---|---|---|
| **Finished-unit user** | Assembled and wired, firmware flashed, **calibrated** (servo zeros and IMU accel zeros baked), **tested** (all four get-up directions verified per unit) | Go straight to [08 usage](./08-self-righting) and [09 WiFi/twin](./09-wifi-twin) (optional); keep [10](./10-troubleshooting)/[11](./11-reference) for reference. **Pages 02/03/04/06/07 are only needed for firmware upgrades, servo/IMU replacement or horn re-mounting**; to use the twin/telemetry tools on page 09, first install the computer-side tools from page 02. |
| **Kit / DIY builder** | Starts from parts | Follow [01](./01-basics) → [02](./02-environment) → [03 flash](./03-build-flash) → [04 assembly](./04-assembly) → [05](./05-debug-and-checks) → [06 zeroing (required)](./06-zero-tool) → [07](./07-calibrate) → [08](./08-self-righting) end to end. Both servo zeroing (06) and IMU calibration (07) happen **after full assembly and flashing**: `z` does not use the IMU and works in any pose; `c` needs the assembled robot standing level. |

> Recommended first-use check for a finished unit: power up upright → confirm `up≈(0,0,1)` →
> tip it once in each of the four directions per [page 08](./08-self-righting) and
> confirm it stands up.

## Prerequisites

- SR-Support mechanical parts (bottom plate, shoulder servo mount, elbow servo mount, top strut; printing and assembly on [page 04](./04-assembly));
- ESP32-S3 board, Juxi ICM42670P IMU, passive direct-drive servo adapter board;
- 2× PTK7452MG (180° PWM) servos;
- A servo power supply (spec 6 V / ≥5 A) and a USB-C data cable;
- A computer with the environment from [page 02](./02-environment).

## Verified status (2026-11-06)

All four fallen directions have been verified on the real robot, each as a **direct get-up**
(no roll-over needed), taking about 1–6 s; no servo envelope violations were recorded. The
kit also ships an arrow-key zero calibration tool ([page 06](./06-zero-tool)), a WiFi status
page with home-network provisioning, and a wireless MuJoCo live twin
([page 09](./09-wifi-twin)).

## Safety

> - Hold the robot on first power-up, keep a 30 cm clear area, and send `x` or cut servo power
>   on any anomaly;
> - Never stall a servo longer than 1 s; stop when the case exceeds 60 °C;
> - the servo supply **5 V / ≥5 A is verified for all four get-up directions** (6 V gives
>   more margin);
> - 6 V goes to the servo rail only - **never** to the ESP32 5V/3V3 (a 5 V supply may feed the
>   ESP32 5V pin);
> - Everything shares one ground; power-up order is in [page 04](./04-assembly).
