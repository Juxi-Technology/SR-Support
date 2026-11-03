"""Reference get-up target-angle sequences for the 4 cm b39 build.

The pitch sequences were produced by tools/search_b39_getup.py (the original
SelfRisingRobot search_all_getup.py method): coarse target-waypoint patterns
plus random sequences, scored in the 0.25/0.2 ms MuJoCo model with an
arm-penetration penalty. Waypoints are (shoulder, elbow) target angles in rad.

The roll_pos sequence is the original searched three-waypoint lift, the
motion that works on the real robot. The servo PWM output is clamped to
SERVO_MAX_US (500..2500 us with the shoulder centered at 1840 us), so the
arm physically tops out near +1.04 rad even though the config range says
+2.07 - the real machine gets up within that reduced travel, i.e. the
usable range is nearly symmetric [-1.07, +1.04]. Rotating the working
roll_pos press by 180 deg about the shoulder axis maps q1 -> q1 + pi, so
+2.0 mirrors to -1.14, just past the -1.07 stop. roll_neg is therefore
that mirror press: shoulder to -1.07, elbow folded +0.8. On the 6 V bench
the shoulder-only press levers the lying body straight up (~3.5 s total,
hardware 2026-10-30). On the 5 V rail it stalls at up_z ~0.60, right at
the base-rim lever limit, so the sequence now adds a second motor and an
impact: lift the arm off the floor, slam into the press, then pump ELBOW
WEDGES (shoulder held at -1.07, elbow 0.8 -> 0.15 -> 0.8). A kinematic
probe of the recorded stall attitude (logs/kick_probe.py) shows that
extending the elbow drives the forearm tip deeper toward the floor and
lengthens the contact lever while the shoulder reaction stays zero - the
floor reaction lifts the body where the static press runs out of torque.
(Probe: tools/probe_v1_kick_geometry.py.)
Re-folding only slides the tip inward (the rim holds the body), so the
wedges ratchet. The firmware additionally holds capped phases while the
body is down and exits to the retract as soon as it is upright
(getup_executor.HOLD_TICKS / HOLD_UP, firmware EXEC_R1_HOLD).
The previous over-the-top roll recipe needed the +X-side travel that the
PWM clamp does not provide.
"""

from __future__ import annotations

import numpy as np

SEQUENCES = {
    "roll_pos": [
        [2.0, -0.8],
        [0.0, -0.8],
        [0.0, 0.0],
    ],
    "roll_neg": [
        # Mirror press with a second motor: wind-up, slam, adaptive press,
        # then three elbow wedges with re-folds between them. The last row
        # is the retract trigger, as in every sequence.
        [0.6, 0.8],      # wind-up off the floor
        [0.6, 0.8],      # brake
        [-1.07, 0.8],    # slam into the press
        [-1.07, 0.8],    # adaptive press hold (<=50 ticks, firmware)
        [-1.07, 0.15],   # elbow wedge 1
        [-1.07, 0.15],   # adaptive hold (<=40)
        [-1.07, 0.8],    # re-fold (re-cock the elbow)
        [-1.07, 0.15],   # elbow wedge 2
        [-1.07, 0.15],   # adaptive hold (<=40)
        [-1.07, 0.8],    # re-fold
        [-1.07, 0.15],   # elbow wedge 3
        [-1.07, 0.15],   # final hold (<=100)
        [0.0, 0.0],      # retract
    ],
    "pitch_pos": [
        [-1.07, 1.55],
        [0.0, 1.55],
        [0.0, 0.0],
    ],
    "pitch_neg": [
        [-1.07, -1.55],
        [0.0, -1.55],
        [0.0, 0.0],
    ],
}


def getup_sequence_for_pose(pose: str) -> np.ndarray:
    return np.asarray(SEQUENCES[pose], dtype=np.float64)
