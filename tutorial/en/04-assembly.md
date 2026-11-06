---
title: 04 Assembly: print, build, wire
description: Printing, servo horn re-index and centering, wiring table, IMU mounting orientation and power-up order for SR-Support.
---

# 04 Assembly: print, build, wire

> **Finished-unit users can skip this page**: the factory has already printed, assembled, wired
> and inspected the unit (see the factory-state section in [index](./index)). Follow this page
> only when building from parts or replacing components.

## 4.1 Printing and inspection

1. Print `footP`, `arm1P`, `arm2P` and `armhornP` ×2;
2. Check the base outline (~60 × 73 mm) and the 37 mm riser with calipers; the foot plate is
   3 mm, total base height 40 mm;
3. Test-fit the 25T servo horns in their slots; fix with screws only when there is no bind;
4. Weigh every printed part and record it for later simulation mass calibration.

## 4.2 Servo preparation (electrical center and horn index)

1. **Electrical center (before assembly)**: connect only the two servo signals (GPIO4/5) plus
   servo power and common ground, flash the `firmware/servo_center_ptk` bench sketch; both
   servos output 1520 µs and you install the horns facing up (the sketch uses no IMU and is
   only for mechanical centering);
2. **Re-index the shoulder horn** by about 2 teeth (~29°) on the 25T spline so that the firmware
   center pulse (current baked value **1681 µs**, `SERVO_SHOULDER_CENTER_US`) corresponds to a
   vertical arm at `q=0`; the elbow follows the same logic (**1456 µs**, `SERVO_CENTER_US`);
3. Mount the horns, tighten, and check the full travel by hand for binding;
4. Direction convention (matches the simulator): `shoulder +q` moves the big arm toward **−Y**,
   `elbow +q` moves the forearm toward **+X**; firmware defaults are
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> The horn index is only a **coarse centering**. The precise zero must be set after full
> assembly and main-firmware flashing ([page 05](./05-step1-build-flash)) with the
> [page 02 zero tool](./02-zero-tool): declare the visually vertical pose q=0 (`z` does not
> use the IMU and works in any pose), then bake the printed pulses into `config.h` and reflash.
> Even if you skipped the 1520 µs pre-centering and assembled directly, this zeroing still
> works; only when one side lacks travel (the pulse clamps at 500/2500 µs) do you need to pull
> the horn and re-index. The horn index sets how the travel splits between the two sides; the
> firmware manual limits (`Q_SHOULDER_MIN/MAX`) must match the real travel - do not widen them.
> After zeroing, shift all sequence waypoints as described on page 02, otherwise the physical
> get-up poses drift.

## 4.3 Base and arm assembly

1. Fix the 3 mm foot plate to the 37 mm riser with M3 screws to form the 40 mm base;
2. Install the shoulder servo in the top slot, horn facing up;
3. Attach `arm1P` (upper arm) to the shoulder horn and tighten;
4. Install the elbow servo at the top of `arm1P`; connect `arm2P` (forearm) through `armhornP`;
5. Move the arm to vertical by hand (`q≈0`) and confirm it matches the servo center.

## 4.4 Wiring

| Device | ESP32-S3 pin | Adapter | Notes |
|---|---|---|---|
| Shoulder signal | GPIO4 | CH1 | 50 Hz PWM |
| Elbow signal | GPIO5 | CH2 | 50 Hz PWM |
| IMU SDA | GPIO6 | CH3 signal pin | I²C 0x23, 100 kHz |
| IMU SCL | GPIO7 | CH4 signal pin | I²C 0x23, 100 kHz |
| IMU VCC | 3V3 | — | **Never to servo V+ (6 V)** |
| IMU GND | GND | CH3/CH4 GND | Common ground |
| LED (optional) | GPIO2 | — | Status LED |
| Servo V+ | — | V+/GND terminal | 6 V / ≥5 A |
| Servo GND | — | V+/GND terminal | Common with ESP32 |

Notes:

- The adapter is passive: confirm every cascaded header has the same V+/GND/signal order -
  reversed polarity destroys servos or the board;
- Keep I²C wires short and away from servo wires; module pull-ups are 3.3 V;
- On first power-up leave the servos disconnected, verify V+ polarity and voltage with a
  multimeter, then test one servo, then both;
- Power-up order: ground and signals → servo power → ESP32 USB. Reverse when powering down.

## 4.5 IMU mounting orientation

The IMU is mounted rotated +90° about the body vertical. The firmware enables `IMU_YAW90` and
converts the IMU-frame up vector into body coordinates:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

After mounting, verify with [page 03](./03-debug-and-checks): upright gives `up≈(0, 0, 1)`;
the four lying poses are listed in the table in 3.4.
