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
that mirror press: shoulder to -1.07, elbow folded +0.8, hold ~1.6 s; the
arm levers the lying body straight up onto its base (hardware-tested
2026-10-30, ~3.5 s end to end). The previous over-the-top roll recipe
needed the +X-side travel that the PWM clamp does not provide.
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
        # 180 deg-rotation mirror of the roll_pos press: shoulder to the
        # -1.07 stop with the elbow folded the mirrored way (+0.8), hold
        # ~1.6 s, then retract. The arm levers the lying body straight up
        # onto its base - no over-the-top roll. Hardware-verified
        # 2026-10-30 (body upright ~0.8 s after the press, ~3.5 s total).
        [-1.07, 0.8],
        [-1.07, 0.8],
        [-1.07, 0.8],
        [-1.07, 0.8],
        [0.0, 0.8],
        [0.0, 0.0],
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
