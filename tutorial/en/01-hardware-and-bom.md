---
title: 01 Hardware and BOM
description: SR-Support specifications, bill of materials, tools and power safety requirements.
---

# 01 Hardware and BOM

## 1.1 Overview

SR-Support is a 2-DOF (shoulder + elbow) active self-righting device. After falling it plants
its arm on the ground, rolls and levers itself back upright.

| Item | Specification |
|---|---|
| Base | 8.5 × 8.5 cm square; total height 4 cm (37 mm riser + 3 mm foot plate) |
| Arm | About 26 cm tall when upright (upper arm + forearm) |
| Mass | About 102 g with both servos and electronics (to be calibrated by weighing) |
| Shoulder | PTK7452MG, usable travel about [-1.07, +2.07] rad after horn re-indexing |
| Elbow | PTK7452MG, usable travel about ±1.55 rad |
| Controller | ESP32-S3-DevKitC-1 (Arduino framework / PlatformIO) |
| Attitude | Juxi ICM42670P 6-axis IMU (I²C address 0x23, 100 kHz) |
| Servo drive | ESP32 LEDC, 50 Hz, 14 bit, 500–2500 µs pulse width |

## 1.2 BOM

| Category | Part | Qty | Notes |
|---|---|---|---|
| Structure | 3D printed `footP` / `arm1P` / `arm2P` / `armhornP` | 1 / 1 / 1 / 2 | PETG or PLA; weigh after printing |
| Actuation | PTK7452MG 180° PWM servo | 2 | Metal gear, 25T, ~12.2 g, ~3.4 kg·cm at 6 V |
| Controller | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Adapter | Passive servo adapter board | 1 | GPIO → 3-pin headers, shared V+/GND, no PCA9685 |
| Sensor | Juxi ICM42670P IMU module | 1 | 3.3 V supply |
| Power | 6 V / ≥5 A servo supply | 1 | Separate from the ESP32 |
| Power | Electrolytic 1000–2200 µF + 100 nF | 1 each | At the servo supply terminals |
| Power | 5 A fuse / resettable fuse + switch | 1 set | — |
| Wiring | USB-C data cable, Dupont wires, servo extensions | several | — |
| Fasteners | M2/M3 screws, zip ties, rubber O-rings | several | O-rings for tip grip |

## 1.3 Tools

- Calipers and a multimeter (continuity/voltage);
- Screwdrivers and hex keys;
- A computer with PlatformIO (recommended) or Arduino IDE;
- Optional: servo tester, INA219 current monitor.

## 1.4 Power and safety

- Power the 2× PTK7452MG from a **6 V / ≥5 A** supply; 7.4 V reaches ~4.5 kg·cm but heat and
  current must be measured;
- Add 1000–2200 µF plus 100 nF at the servo supply, a 5 A fuse and a power switch;
- Power the ESP32 separately from USB-C 5 V and tie the grounds together;
- **Never connect 6 V/7.4 V to the ESP32 5V/3V3**, and never drive both servos from a PC USB port;
- Power-up order: ground and signals first → servos → ESP32. Reverse when powering down.
