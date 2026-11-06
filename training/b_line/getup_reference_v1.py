"""Sim-only get-up references for the v1 CAD model.

The deployed references in getup_reference_b39.py are the hardware set. Its
roll_neg entry is hardware-specific (swing the arm over the top, roll the
body, then let the pose re-plan take over with the pitch reference) and does
not transfer to MuJoCo. This module keeps the four references with a
sim-searched roll_neg for the v1 model (hardware/v1/robot_v1.xml).

roll_neg (v1 sim): the get-up mechanism itself is mirror-symmetric - both
roll directions need about 1.4 rad of shoulder travel to press the floor
and lever the body up (1.4 rad works and 1.2 fails on both sides). The
re-indexed 180 deg shoulder spans -1.07..+2.07 rad, which starves the
negative side (0.61 rad): the arm hits the -1.07 stop with the body
levered to ~47 deg (base edge + strut-tip tripod). On this servo this
sequence is the best motion within range: it yaws the lying body 90 deg
onto the pitch axis (flat, up_z never below the lying value) and then
runs the pitch lift - no over-the-top roll. ~226 ticks, one re-plan.

Proven fix (sim; the robot_v1_sym variant file has since been removed
from the repo during the 2026-11 slimming, kept here as a record):
re-index the shoulder horn to center the 180 deg window (same servo, no
new part). Then roll_neg gets up directly: press the shoulder to -1.5 and
hold ~2 s, the body tips straight up onto its base face - ~175 ticks,
zero pose switches, min_upz +0.04, 9/9 at +-10 deg lie perturbations.
roll_pos works unchanged at +1.57 (110 ticks) and the pitch references
are untouched (q1=-1.07 stays inside the new range). 4/4 direct get-ups
verified on that model.

Hardware continues to use getup_reference_b39.py; do not flash this sequence.
"""

from __future__ import annotations

from .getup_reference_b39 import SEQUENCES

ROLL_NEG_V1_SIM = [
    [-0.721355, -1.454908],
    [-1.051076, 0.649395],
    [1.797237, 0.568705],
    [0.0, 0.0],
]

# References for the centered +-1.57 shoulder (robot_v1_sym.xml, the horn
# re-index proposal): direct single-side get-up in both roll directions.
ROLL_POS_V1_SYM = [[1.57, -0.8], [0.0, -0.8], [0.0, 0.0]]
ROLL_NEG_V1_SYM = [[-1.5, 0.0]] * 4 + [[0.0, 0.0]]

SEQUENCES_V1 = dict(SEQUENCES)
SEQUENCES_V1["roll_neg"] = ROLL_NEG_V1_SIM

SEQUENCES_V1_SYM = dict(SEQUENCES)
SEQUENCES_V1_SYM["roll_pos"] = ROLL_POS_V1_SYM
SEQUENCES_V1_SYM["roll_neg"] = ROLL_NEG_V1_SYM


def getup_sequence_for_pose_v1(pose: str):
    import numpy as np
    return np.asarray(SEQUENCES_V1[pose], dtype=np.float64)
