---
title: 06 Zero-calibration (arrow keys; required for DIY builds)
description: Jog the arm to the visual center with arrow keys and declare it q=0; required for every DIY build, and after re-indexing a horn or re-assembly.
---

# 06 Zero-calibration (arrow keys; required for DIY builds)

The servo zeros and the IMU accel zeros are calibrated and baked per unit at the factory, so a
stock unit needs nothing here. A **DIY build must do this page**: a hand-assembled arm will
almost never sit exactly at the center. Even if you never powered the servos to their 1520 µs
center and just assembled the robot directly, you can still fix it here - jog the arm to
visually vertical with the arrow keys and press `z` to declare the **current** pose q=0. The
`z` command does not use the IMU and works at any pose or horn index.

Come back when: a horn was re-indexed, the arm was disassembled/re-assembled, a servo was
replaced, the IMU was replaced/re-mounted (recalibrate the accel), or the arm no longer rests at
the visual center after retracting.

> `z` only shifts the software zero; it does **not** change how the horn index splits the travel
> (PWM 500-2500 µs). If after zeroing one direction runs out of range (the pulse clamps at
> 500/2500 µs and the arm cannot reach a required sequence angle), re-index the horn (~2 teeth
> from the 1520 µs center on the shoulder) and zero again.

Timing: after the robot is fully assembled and the main firmware is flashed (the DIY path
runs 03 → 04 → 05 → 06).

## 6.1 Principle

The firmware defines q=0 as the visual center: arm vertical, both links in one line. The `z`
command is an encoder-style zero: it makes the **current** joint positions q=0 and prints the
corresponding center pulse widths.

## 6.2 Procedure

1. Connect both the battery and USB (servos powered) and run this in the `SR-Support` folder
   with `.venv` activated:

   ```bash
   python tools/hw_shoulder_range.py
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

## 6.3 Baking (mandatory once satisfied)

`z` only touches RAM; a reboot restores the old zero. When happy:

1. Write the two pulse values into `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. Shift every waypoint of `EXEC_REF*` and `training/b_line/getup_reference_b39.py` by the same
   offsets (shoulder/elbow each −Δ rad);
3. Reflash and re-test all four directions ([page 08](./08-self-righting)).

> A mis-press is harmless: zero again to overwrite.

## 6.4 Related commands

| Command | Function |
|---|---|
| `z` | Current pose becomes q=0 for both joints; prints the new center pulses (RAM only) |
| `k` | Read the current center pulses (shoulder/elbow, µs) |
| `o` / `p` | Shoulder center ±10 µs live trim (reset on reboot) |
