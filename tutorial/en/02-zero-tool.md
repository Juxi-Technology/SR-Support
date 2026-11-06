---
title: 02 Zero-calibration tool (arrow keys, skippable)
description: Jog the arm to the visual center with arrow keys and declare it q=0 with one command; required after re-indexing a horn or re-assembly.
---

# 02 Zero-calibration tool (arrow keys, skippable)

The servo zeros and the IMU accel zeros are calibrated and baked per unit at the factory, so
**you can skip this page** for a stock unit. Come back when: a horn was re-indexed, the arm was
disassembled/re-assembled, a servo was replaced, the IMU was replaced/re-mounted (recalibrate
the accel), or the arm no longer rests at the visual center after retracting.

This page sits at position 02 only because it is a standalone tool page; **in practice it is
used after [page 04 assembly](./04-assembly) and [page 05 flashing](./05-step1-build-flash)**.
The `z` command only reads the current servo command positions and does not use the IMU, so it
works in any pose - but it only makes sense once the robot is fully assembled.

## 2.1 Principle

The firmware defines q=0 as the visual center: arm vertical, both links in one line. The `z`
command is an encoder-style zero: it makes the **current** joint positions q=0 and prints the
corresponding center pulse widths.

## 2.2 Procedure

1. Connect both the battery and USB (servos powered) and run:

   ```bash
   .venv/Scripts/python.exe tools/hw_shoulder_range.py
   ```

   A persistent three-line display updates in place:

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Jog with the arrow keys: `↑`/`↓` = big arm ±0.05 rad, `←`/`→` = small arm ±0.05 rad
   (Shift = ±0.20) until the arm looks **vertical and aligned**;
3. Press `z`; the firmware prints:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. Sanity check: press `n` (home), jog a little, home again - the arm must return to the visual
   center you just defined.

## 2.3 Baking (mandatory once satisfied)

`z` only touches RAM; a reboot restores the old zero. When happy:

1. Write the two pulse values into `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. Shift every waypoint of `EXEC_REF*` and `training/b_line/getup_reference_b39.py` by the same
   offsets (shoulder/elbow each −Δ rad);
3. Reflash and re-test all four directions ([page 07](./07-step3-self-righting)).

> A mis-press is harmless: zero again to overwrite.

## 2.4 Related commands

| Command | Function |
|---|---|
| `z` | Current pose becomes q=0 for both joints; prints the new center pulses (RAM only) |
| `k` | Read the current center pulses (shoulder/elbow, µs) |
| `o` / `p` | Shoulder center ±10 µs live trim (reset on reboot) |
