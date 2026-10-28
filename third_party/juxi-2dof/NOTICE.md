# NOTICE

Copyright (c) 2026 Juxi Technology.

## Third-party components

- **Feetech SCServo** (`firmware/lib/scservo/`): GPL-3.0. Copyright its
  original authors. See `firmware/lib/scservo/LICENSE`.
- **Juxi ICM42670P IMU module**: protocol and register information was read
  from the public Juxi-Technology repository
  (https://github.com/Juxi-Technology/ICM42670P-High-Precision-IMU-Module).
  No vendor source code is copied into this repository.
- **HomeMadeGarbage SelfRisingRobot**: used only as a public design reference.
  The reference repository has no license; this repository contains no code or
  STL from it. The B-line scripted-pretraining data in `sim/expert_test.py`
  contains numeric waypoint values published there. Before public
  distribution, obtain permission for those values or replace them with
  locally generated waypoints.

## Firmware binaries

- A-line `scs0009` firmware links the GPL-3.0 SCServo library, so that binary
  is distributed under GPL-3.0. Source is this repository.
- B-line `sg90` firmware does not link SCServo; it is covered by the
  MIT/Apache-2.0 terms above.
