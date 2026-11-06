---
title: 06 Debug and calibration
description: Telemetry format, IMU and servo checks, gyro+accel calibration, center check, four lying poses and the fall gate, done criteria.
---

# 06 Debug and calibration

> **Finished-unit users can skip this page**: the factory calibrates and verifies every unit.
> Redo these steps only after replacing a servo/IMU, re-mounting a horn, or when a firmware
> upgrade is suspected to have disturbed the calibration.

This is the **whole-robot functional check and calibration** after assembly, flashing and
zeroing; work through it in order before using the robot.

> **Power while debugging**: USB carries serial data only. `c` needs just the IMU (the
> servos may stay unpowered); `t` / `z` / `e` need the 5 V servo rail on. If you do not want
> the ESP32 fed from two sources, unplug the 5 V branch to the ESP32, power it from USB alone
> and let the 5 V supply feed only the servos - a normal setup, see
> [page 04, section 4.4](./04-assembly.md).

## 6.1 Open the serial port and read telemetry

In the `SR-Support` folder with `.venv` activated, open the serial port (`COM27` is your port):

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Serial tools / the Windows UartAssist download are on
[page 03, section 3.3](./03-build-flash.md).)

Opening the port resets the ESP32; you should see the boot log and then one telemetry line
every 250 ms:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Field | Meaning | How to read it |
|---|---|---|
| `up` | World up vector in body coordinates (x forward, y left, z up) | upright `(0,0,1)`, tilt≈0°; lying poses in 6.5 (e.g. `(-1,0,0)`=pitch_pos) |
| `w` | Angular velocity (rad/s) | ≈0 when still; non-zero while getting up/rolling; the fall gate needs `|w|<0.9` |
| `q` | Current joint **command** angles (shoulder, elbow, rad; no feedback) | q=0 is arm vertical; shoulder + → big arm toward −Y, elbow + → forearm toward +X |
| `qd` | Joint command rates | rarely needed |
| `mode` | Run mode | `run` / `hold` / `manual` / `auto` |

Example readings (`hw_watch` window):

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

`tilt` is the angle between the up vector and vertical (from `up_z`); 0° means fully upright.

If the scrolling stream is hard to read, use the fixed-line live window (commands still work):

```bash
python tools/hw_watch.py --port COM27
```

It redraws up/tilt, angular velocity, joint angles, mode and the last event in place; type at
`cmd>` and press Enter to send a command, and events are also appended to
`logs/hw_watch.log`. For a full get-up run where every raw line matters, keep using
`pio device monitor` or `tools/hw_monitor.py` (the latter writes a summary to the log every
5 s).

**How to send serial commands**: keep the monitor open and type the command followed by
Enter (single-character commands need no quotes). Commands used on this page:

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

The full command table is on [page 03, section 3.4](./03-build-flash.md).

**Quick self-check script** (close the serial monitor first so the port is free):

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

The first command reads 0.6 s of telemetry; during `--tilt 8` tilt the robot by hand and it
prints the up/gyro ranges and the tilt range, which reveals a stuck or mis-oriented IMU.

## 6.2 IMU checks and calibration

`c` does two things:

1. **Gyro zero bias**: averages 200 still samples (about 2 s) into the zero-rate offset; this
   is used for the current power cycle and is redone automatically on every boot;
2. **Accelerometer zero**: from the same samples it averages the gravity vector, requiring the
   robot to stand level (gravity entirely on +Z), sanity-checks it and stores it in NVS
   (reloaded on boot).

Procedure (servo power is not required):

1. Stand the robot upright on a LEVEL table, hands off, cables not pulling;
2. Type `c` and press Enter in the serial monitor or the `hw_watch` `cmd>`:

   ```text
   c
   ```

3. Keep still for about 2 s; success prints:

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

4. `accel cal rejected: |a|=...` means the robot was not level or not still (the gravity norm
   is more than 1.5 m/s² away from 9.8); the bias is left unchanged - place it again and
   resend `c`.

Verification:

- Tilt slowly left/right and forward/back: the x/y components of `up` must follow smoothly;
  if a direction is reversed, send `i` / `j` to flip the IMU axis sign and run `c` again;
- Place the robot down and wait 2 s: `up` must match the lying-pose table in 6.5 (e.g.
  `(0,-1,0)` = roll_neg) with the base face flat;
- A persistent 5°+ tilt while lying usually means the accel zero is off - redo this section.

> Finished units are calibrated at the factory (stored in NVS); redo this only after
> replacing/re-mounting the IMU or when the lying pose is visibly tilted. `c` only calibrates
> the IMU - it does not change the servo zero (that is [page 05](./05-zero-tool.md)).
>
> If you used manual commands before calibrating (the telemetry ends in `manual`), `c` leaves
> the robot in `hold`/`manual` and the fall gate will not start a get-up; keep it upright and
> send `g` to resume, or reset the board.

## 6.3 Servo checks and direction self-test

| Check | Method | Expected |
|---|---|---|
| Centers | `k` | `centers: shoulder 1681 us, elbow 1456 us` (visual-center values baked 2026-11; re-zero per [page 05](./05-zero-tool.md)) |
| Shoulder trim | `o` / `p` (±10 µs) | Arm vertical at `q=0` |
| Direction | `m 0.5 0` / `m 0 0.5` | Shoulder + → big arm toward −Y; elbow + → forearm toward +X |
| Sign flip | `v` (shoulder) / `b` (elbow) | Only if a direction is reversed |
| Self-test | `t` | Small motion on both joints, then center |
| Neutral | `m 0 0` or `r` | Arm vertical |

Joint limits:

- Shoulder manual commands `[-1.85, +1.82]` rad; elbow mechanical `±1.55` rad (reachable by the
  executor);
- Manual `m` commands clamp the elbow to `[-0.90, +0.70]` rad;
- PWM output 500–2500 µs at 50 Hz.

Type these one by one into the **send box** of the serial monitor/assistant (Enter after each):

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Confirm: shoulder `q>0` → big arm toward **−Y**; elbow `q>0` → forearm toward **+X**.
Wrong direction: flip with `v` / `b`, or re-mount the horn.

## 6.4 Center check

Baked at the factory (shoulder 1681 µs / elbow 1456 µs) - **skippable for a stock unit**. In a
DIY build this was already done with the [page 05 zero-calibration](./05-zero-tool.md) and the
values baked into `config.h` (reflash if they changed); here just run `k` to confirm the
centers match the baked values. Return to page 05 only after re-indexing a horn, re-assembly,
or if the arm no longer rests at the visual center.

## 6.5 Four lying poses and the fall gate

| Pose | Monitor `up` | Physical meaning |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | Body top points toward +X |
| `pitch_neg` | `(+1, 0, 0)` | Body top points toward −X |
| `roll_pos` | `(0, +1, 0)` | Body top points toward −Y |
| `roll_neg` | `(0, -1, 0)` | Body top points toward +Y |

Fall-gate condition (firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Only then does it print `getup start pose=...` and begin. So place the robot, release it and
keep it still for ~0.5 s; waving it around right after placing usually means a hand is still
touching it or the body is still rolling.

Check: place the robot in each of the four poses, release and keep still; within 0.5 s the
serial log must show `getup start pose=<matching pose>`.

## 6.6 Done criteria

- [ ] `c` prints `accel bias ... (saved)`;
- [ ] `t` shows correct directions on both joints;
- [ ] `k` matches the baked centers (or you re-zeroed per page 05 and baked it);
- [ ] all four lying poses trigger `getup start`.

---

[← Back to the tutorial contents](./index.md)
