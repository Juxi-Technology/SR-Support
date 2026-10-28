---
title: SR-Support Self-Righting Robot Tutorial
description: Complete tutorial for the SR-Support 2-DOF self-righting device, from hardware and assembly to firmware, self-righting usage and troubleshooting.
---

# SR-Support Self-Righting Robot Tutorial

SR-Support is a low-cost active self-righting device based on a 2-DOF arm. After tipping in
any direction it plants its two-joint arm on the ground, rolls and levers itself back upright.

## What you will build

| Chapter | Content |
|---|---|
| [01 Hardware and BOM](./01-hardware-and-bom) | Specifications, BOM, tools, power safety |
| [02 Assembly and Wiring](./02-assembly-and-wiring) | Printed parts, horn re-index, wiring table, IMU mounting |
| [03 Firmware Build and Flash](./03-firmware-build-and-flash) | PlatformIO build, flashing, serial commands |
| [04 Calibration and Checks](./04-calibration-and-checks) | IMU attitude, servo direction/center, fall gate |
| [05 Self-Righting Usage](./05-self-righting-usage) | Placement, expected motion, monitoring and logs |
| [06 Troubleshooting](./06-troubleshooting) | Common symptoms and fixes |
| [07 Parameters and References](./07-parameters-and-references) | Firmware parameters, reference sequences, licensing |

## Prerequisites

- Printed and assembled SR-Support mechanical parts (`footP`, `arm1P`, `arm2P`, `armhornP` ×2);
- ESP32-S3 board, Juxi ICM42670P IMU, passive direct-drive servo adapter board;
- 2× PTK7452MG (180° PWM) servos;
- 6 V / ≥5 A servo power supply and a USB-C data cable;
- PlatformIO (recommended) or Arduino tooling on your computer.

## Verified status (2026-10-27)

All four fallen directions have been verified on the real robot: the two pitch directions take
about 3–6 s; the shoulder-swing direction (`roll_neg`) rolls over the top and re-plans to the
pitch reference, taking 5–14 s. No servo envelope violations were recorded.

## Safety

> - Hold the robot on first power-up, keep a 30 cm clear area, and send `x` or cut servo power
>   on any anomaly;
> - Do not stall a servo for more than 1 s; keep the case below 60 °C;
> - 6 V goes to the servo rail only — never to the ESP32 5V/3V3;
> - Common ground for everything; see Chapter 02 for the power-up order.
