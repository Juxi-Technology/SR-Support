"""Reference get-up target-angle sequences for the 4 cm b39 build.

The pitch sequences were produced by tools/search_b39_getup.py (the original
SelfRisingRobot search_all_getup.py method): coarse target-waypoint patterns
plus random sequences, scored in the 0.25/0.2 ms MuJoCo model with an
arm-penetration penalty. Waypoints are (shoulder, elbow) target angles in rad.

The roll_pos sequence is the original searched three-waypoint lift, the
motion that works on the real robot. The roll_neg side cannot plant the arm
on the far side (the horn re-index limits the shoulder to -1.07 rad), and
dragging the forearm on the floor does not transmit enough force on the real
surface, so roll_neg swings the arm over the top and holds: the arm's mass
rolls the body over its long axis and holds it at a pitch-like attitude; the
pose re-plan then hands over to the pitch sequence, whose kick flips the
inverted body onto the +X face and lifts it. A continuous variant that
returned the arm itself was hardware-tested and fails: any arm return rolls
the body back to roll_neg before the pitch kick can act.
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
        # Swing the arm over the top and hold: the arm's mass rolls the body
        # over its long axis and holds it at a pitch-like attitude; the
        # executor's pose re-plan then hands over to the pitch sequence,
        # which kicks the inverted body onto the +X face and lifts it. A
        # continuous version that returns the arm itself first was tested on
        # hardware and fails: any arm return rolls the body back to roll_neg
        # before the pitch kick can act.
        [2.0, -0.8],
        [2.0, -0.8],
        [2.0, -0.8],
        [2.0, -0.8],
        [0.0, -0.8],
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
