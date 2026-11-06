---
title: 04 Assembly: print, build, wire
description: Printing, servo horn re-index and centering, wiring table, IMU mounting orientation and power-up order for SR-Support.
---

# 04 Assembly: print, build, wire

> **Finished-unit users can skip this page**: the factory has already printed, assembled, wired
> and inspected the unit (see the factory-state section in [index](./index)). Follow this page
> only when building from parts or replacing components.

## 4.1 Printing and inspection

1. Print the bottom plate, shoulder servo mount, elbow servo mount and top strut (1 each);
2. Check the base outline (~88 × 82 mm) and total height (~68 mm) with calipers;
3. Test-fit the 25T servo horns in their slots; fix with screws only when there is no bind;
4. Weigh every printed part and record it against `hardware/v1/meshes/print_mass_model.json`.

## 4.2 Servo preparation (firmware zero and horn installation)

1. **Wire and flash first**: wire both servos, the IMU, servo power and the common ground per
   the table in 4.4 (mechanical parts not mounted yet; the main firmware needs the IMU to
   boot), then flash the main firmware per [page 03, section 3.1](./03-build-flash);
2. **Power on to the firmware zero**: open the 115200 serial port (serial tools / the
   UartAssist download are on [page 03, section 3.3](./03-build-flash)) and power up; after boot the
   firmware drives both servos to q=0 (center pulses 1681 / 1456 µs). When the log shows
   `servo start q: 0.00 0.00 rad` and `ready; send g to run` (or `autorun on: ...`), the
   servos are at the zero;
3. **Power off**: cut the servo power (USB may stay connected) and confirm both servos are
   unloaded;
4. **Install the horns**: mount the shoulder horn so the upper arm is vertical, and the elbow
   horn so the forearm is in line with it; tighten and check the full travel by hand;
5. Direction convention (matches the simulator): `shoulder +q` moves the big arm toward **−Y**,
   `elbow +q` moves the forearm toward **+X**; firmware defaults are
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> The firmware centers 1681 / 1456 µs already include the horn re-index from the factory
> calibration - **do not count teeth**: mount the horns at the firmware zero with the arm
> vertical. Alternatively (equivalent, optional) send `e` to put both servos at the 1520 µs
> electrical center and mount there (see the command table on [page 03](./03-build-flash));
> either way the [page 05](./05-zero-tool) `z` command does the final precise zero.

> Mounting at the firmware zero is only a **coarse centering** (the horn spline is discrete).
> The precise zero must be set after full assembly and main-firmware flashing
> ([page 03](./03-build-flash)) with the [page 05 zero tool](./05-zero-tool): declare the
> visually vertical pose q=0 (`z` does not use the IMU and works in any pose), then bake the
> printed pulses into `config.h` and reflash. Even if the horn was not mounted perfectly, this
> zeroing fixes it; only when one side lacks travel (the pulse clamps at 500/2500 µs) do you
> need to pull the horn and re-index. The horn index sets how the travel splits between the two
> sides; the firmware manual limits (`Q_SHOULDER_MIN/MAX`) must match the real travel - do not
> widen them. After zeroing, shift all sequence waypoints as described on page 05, otherwise
> the physical get-up poses drift.

## 4.3 Base and arm assembly

1. Fix the bottom plate and the shoulder servo mount together with M3 screws to form the base
   (~68 mm tall);
2. Install the shoulder servo in the shoulder mount, horn facing up;
3. Attach the elbow servo mount to the shoulder horn and tighten (it forms the upper arm);
   install the elbow servo in the elbow mount;
4. Connect the top strut (forearm) to the elbow horn;
5. Move the arm to vertical by hand (`q≈0`) and confirm it matches the servo center.

## 4.4 Wiring

| Device | ESP32-S3 pin | Adapter | Notes |
|---|---|---|---|
| Adapter 3V3 | 3V3 | S1 signal pin | other end to IMU VCC (3.3 V) |
| Shoulder signal | GPIO4 | S4 | 50 Hz PWM |
| Elbow signal | GPIO5 | S5 | 50 Hz PWM |
| IMU SDA | GPIO6 | S6 signal pin | other end to IMU SDA; I²C 0x23, 100 kHz |
| IMU SCL | GPIO7 | S7 signal pin | other end to IMU SCL; I²C 0x23, 100 kHz |
| IMU GND | GND | — (direct) | common ground |
| LED (optional) | GPIO2 | — | status LED |
| 5 V power input | 5V / GND | — | 1-to-2 cable: one branch to the ESP32, one to the adapter V+/GND for the servos |
| Servo power | — | V+/GND terminal | 5 V / ≥5 A; **higher voltages must use this terminal only, never the ESP32 5V** |
| S2 / S3 | — | — | not connected |

Notes:

- The adapter is a passive pass-through: S1/S6/S7 carry 3V3 / SDA / SCL on their signal
  pins, S4/S5 carry the servo signals; confirm the V+/GND/signal order of every header -
  reversed polarity destroys servos or the board;
- Keep I²C wires short and away from servo wires; module pull-ups are 3.3 V;
- With a **5 V** supply you may feed the ESP32 5V/GND and branch the same supply to the
  adapter V+/GND for the servos; higher voltages (6 V / 7.4 V) must feed the adapter
  V+/GND only and the ESP32 must be powered from USB;
- **With a 5 V battery feeding the ESP32 you may keep the Type-C plugged in**: in the
  official DevKitC-1 schematic each USB VBUS reaches the 5V net through a Schottky diode, so
  there is no back-feed and USB works as data (plus auxiliary power). On a clone board that
  omits the diode, or if you cannot confirm it, unplug the 5 V branch to the ESP32 while
  flashing and power it from USB (option 2);
- **Power while debugging / flashing (both are normal; pick one)**:
  1. the 5 V supply feeds the ESP32 and the servos via the splitter, USB carries data only;
  2. easier to reason about: unplug the 5 V branch to the ESP32, power the ESP32 from USB
     alone and let the 5 V supply feed only the servos.
  Use option 2 for flashing, serial monitoring and `c` calibration; option 1 for standalone
  operation;
- On first power-up leave the servos disconnected, verify V+ polarity and voltage with a
  multimeter, then test one servo, then both;
- Wiring order: ground and signals → 5 V supply (ESP32 and servos together) → USB for the
  serial port when needed. Reverse when powering down.

## 4.5 IMU mounting orientation

The IMU is fixed to the base with screws (its orientation is not adjustable), so the
firmware enables `IMU_YAW90` and converts the IMU-frame up vector into body coordinates:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Mechanical orientation check** (possible once the servos are mounted, before power-up):
using the axes printed on / documented for the IMU module,

- the shoulder servo **output shaft** (the shaft the horn mounts on; also called the horn
  shaft or gear shaft) points toward the IMU **−Y**;
- the elbow servo output shaft points toward the IMU **+X**.

From bottom to top the two servos are **shoulder (lower) → elbow (upper)**; do not swap them
when mounting the horns or wiring.

These two directions are the body's shoulder and elbow axes; if they do not match the
hardware, the IMU or a servo mount is installed the wrong way - fix it before powering up.

After power-up, re-check on [page 06](./06-debug-and-calibrate): upright gives `up≈(0, 0, 1)`;
the four lying poses are listed in the table in 6.5.
