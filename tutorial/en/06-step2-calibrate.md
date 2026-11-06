---
title: 06 Step 2: calibration
description: After flashing, complete gyro+accel calibration, servo self-test, zeroing and the fall-gate check in order.
---

# 06 Step 2: calibration

Complete these four items in order. Details for each live on the referenced pages.

## 6.1 Gyro + accelerometer calibration

Stand the robot LEVEL on a flat surface and keep it still; send `c`:

- Success prints `gyro bias ...` and `accel bias ... (saved)` (the accel zero is stored in NVS
  and reloaded on boot);
- `accel cal rejected` means the robot was not level or not still - retry;
- Details and the lying-pose check: [page 03, section 3.2](./03-debug-and-checks).

## 6.2 Servo direction self-test

Send `t` and confirm:

- Shoulder `q>0` → big arm toward **−Y**; elbow `q>0` → forearm toward **+X**;
- Wrong direction: flip with `v` / `b`, or re-mount the horn
  ([page 03, section 3.3](./03-debug-and-checks)).

## 6.3 Center / zero

Baked at the factory (shoulder 1681 µs / elbow 1456 µs) - **skippable for a stock unit**. Only
after re-indexing a horn, re-assembly, or if the arm no longer rests at the visual center:
re-zero with the [page 02 tool](./02-zero-tool) and bake the printed values into `config.h`,
then reflash.

## 6.4 Fall-gate check

Place the robot in each of the four lying poses (see
[page 03, section 3.4](./03-debug-and-checks)), release and keep still; within 0.5 s the
serial log must show `getup start pose=<matching pose>` and the get-up begins.

## 6.5 Done criteria

- [ ] `c` prints `accel bias ... (saved)`;
- [ ] `t` shows correct directions on both joints;
- [ ] `k` matches the baked centers (or you re-zeroed per page 02 and baked it);
- [ ] all four lying poses trigger `getup start`.
