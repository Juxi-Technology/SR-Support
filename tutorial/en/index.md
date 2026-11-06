---
title: SR-Support Self-Righting Robot Tutorial
description: Complete tutorial for the SR-Support 2-DOF self-righting device, from basics and environment setup to flashing, assembly, zeroing, calibration, self-righting usage and troubleshooting.
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
| 05 | [Zero-calibration](./05-zero-tool) | Arrow-key jog + `z` zeroing (after re-indexing/re-assembly) | **required for DIY builds**; skippable for stock units |
| 06 | [Debug and calibration](./06-debug-and-calibrate) | Whole-robot check and calibration: telemetry, IMU, servos, center check, four lying poses, fall gate | |
| 07 | [Self-righting usage and monitoring](./07-self-righting) | Four fall directions, expected motion, monitoring and logs | |
| 08 | [WiFi and the simulation twin](./08-wifi-twin) | Status page, home-WiFi provisioning, wireless MuJoCo twin | optional |
| 09 | [Troubleshooting](./09-troubleshooting) | Common symptoms and fixes | reference |
| 10 | [Reference: model, parameters, licensing](./10-reference) | Model files (XML/STL), parameters, reference sequences, licensing | reference |

## Factory state of a finished unit (two reading paths)

This tutorial serves two audiences - pick the path that matches yours:

| Reader | Factory state | Recommended path |
|---|---|---|
| **Finished-unit user** | Assembled and wired, firmware flashed, **calibrated** (servo zeros and IMU accel zeros baked), **tested** (all four get-up directions verified per unit) | Go straight to [07 usage](./07-self-righting) and [08 WiFi/twin](./08-wifi-twin) (optional); keep [09](./09-troubleshooting)/[10](./10-reference) for reference. **Pages 02/03/04/05/06 are only needed for firmware upgrades, servo/IMU replacement or horn re-mounting**; to use the twin/telemetry tools on page 08, first install the computer-side tools from page 02. |
| **Kit / DIY builder** | Starts from parts | Follow [01](./01-basics) → [02](./02-environment) → [03 flash](./03-build-flash) → [04 assembly](./04-assembly) → [05 zeroing (required)](./05-zero-tool) → [06 debug/calibration](./06-debug-and-calibrate) → [07](./07-self-righting) end to end. Both zeroing (05) and calibration (06) happen **after full assembly and flashing**: `z` does not use the IMU and works in any pose; `c` needs the assembled robot standing level. |

> Recommended first-use check for a finished unit: power up upright → confirm `up≈(0,0,1)` →
> tip it once in each of the four directions per [page 07](./07-self-righting) and
> confirm it stands up.

## Prerequisites

- SR-Support mechanical parts (bottom plate, shoulder servo mount, elbow servo mount, top strut; printing and assembly on [page 04](./04-assembly));
- ESP32-S3 board, Juxi ICM42670P IMU, passive direct-drive servo adapter board;
- 2× PTK7452MG (180° PWM) servos;
- A servo power supply (5 V / ≥5 A) and a USB-C data cable;
- A computer with the environment from [page 02](./02-environment).

## Verified status (2026-11-06)

All four fallen directions have been verified on the real robot, each as a **direct get-up**
(no roll-over needed), taking about 1–6 s; no servo envelope violations were recorded. The
kit also ships an arrow-key zero calibration tool ([page 05](./05-zero-tool)), a WiFi status
page with home-network provisioning, and a wireless MuJoCo live twin
([page 08](./08-wifi-twin)).

## Safety

> - Hold the robot on first power-up, keep a 30 cm clear area, and send `x` or cut servo power
>   on any anomaly;
> - Never stall a servo longer than 1 s; stop when the case exceeds 60 °C;
> - the servo supply **5 V / ≥5 A** (verified for all four get-up directions);
> - anything above 5 V goes to the servo rail only - **never** to the ESP32 5V/3V3;
> - Everything shares one ground; power-up order is in [page 04](./04-assembly).
