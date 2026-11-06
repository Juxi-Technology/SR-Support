---
title: 04 Assembly: print, build, wire
description: Printing, servo horn re-index and centering, wiring table, IMU mounting orientation and power-up order for SR-Support.
---

# 04 Assembly: print, build, wire

## 4.1 Printing and inspection

1. Print `footP`, `arm1P`, `arm2P` and `armhornP` ×2;
2. Check the base outline (~60 × 73 mm) and the 37 mm riser with calipers; the foot plate is
   3 mm, total base height 40 mm;
3. Test-fit the 25T servo horns in their slots; fix with screws only when there is no bind;
4. Weigh every printed part and record it for later simulation mass calibration.

## 4.2 Servo preparation (horn re-index)

1. Before mounting, command both servos to 1520 µs (electrical center);
2. **Re-index the shoulder horn** by about 2 teeth (~29°) on the 25T spline so the vertical arm
   corresponds to the firmware zero `q=0`. After re-indexing, define the visual center as q=0
   with the [page 02 zero tool](./02-zero-tool) and write the printed pulse back to
   `SERVO_SHOULDER_CENTER_US` (current unit's baked value: **1681 µs**);
3. The elbow zero follows the same page-02 procedure (current baked value: **1456 µs**,
   `SERVO_CENTER_US`);
4. Mount the horns, tighten, and check the full travel by hand for binding;
5. Direction convention (matches the simulator): `shoulder +q` moves the big arm toward **−Y**,
   `elbow +q` moves the forearm toward **+X**; firmware defaults are
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> The horn index sets how the travel splits between the two sides; the firmware manual limits
> (`Q_SHOULDER_MIN/MAX`) must match the real travel - do not widen them. After zeroing, shift
> all sequence waypoints as described on page 02, otherwise the physical get-up poses drift.

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
