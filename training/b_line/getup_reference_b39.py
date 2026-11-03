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
WEDGES (shoulder held at the stop, elbow 0.8 -> 0.15 -> 0.8). A kinematic
probe of the recorded stall attitude (tools/probe_v1_kick_geometry.py)
shows that extending the elbow drives the forearm tip deeper toward the
floor and lengthens the contact lever while the shoulder reaction stays
zero - the floor reaction lifts the body where the static press runs out
of torque.
Re-folding only slides the tip inward (the rim holds the body), so the
wedges ratchet. Hardware (2026-11-03): the wedges add a
repeatable +0.05 up_z at the press stall (0.60 -> 0.65), matching the sim,
but 0.65 is still short of the balance line, so the press target moved to
-1.45 (see above). The firmware additionally holds capped phases while
the body is down and exits to the retract as soon as it is upright
(getup_executor.HOLD_TICKS / HOLD_UP, firmware EXEC_R1_HOLD).
The previous over-the-top roll recipe needed the +X-side travel that the
PWM clamp does not provide.
"""

from __future__ import annotations

import numpy as np

# Zero frame: visual-center zero 2026-11-03 (shoulder 1681 us,
# elbow 1456 us). Every target is (old value - 0.25 / - 0.10);
# the physical poses match the verified all-directions run.
SEQUENCES = {
    "roll_pos": [
        [1.75, -0.90],
        [-0.25, -0.90],
        [0.0, 0.0],
    ],
    "roll_neg": [
        # Stage 1 opens exactly like roll_pos: one full-speed press (20
        # ticks) to the travel limit, then elbow-wedge pumps. A slow press
        # variant was measured to change nothing (the loaded horn barely
        # rotates either way) and visibly lagged behind the +X side, so
        # the speed now matches roll_pos. Stage 2 retries with the
        # whip-slam (elbow tucked in the air, extension lands at floor
        # contact). Last row = retract trigger.
        [-1.80, 0.70],   # direct press (same slew as roll_pos)
        [-1.80, 0.70],   # adaptive press hold (<=40 ticks, firmware)
        [-1.80, 0.35],   # elbow wedge 1
        [-1.80, 0.05],
        [-1.80, 0.05],   # adaptive hold (<=30)
        [-1.80, 0.70],   # re-fold (re-cock the elbow)
        [-1.80, 0.35],   # elbow wedge 2
        [-1.80, 0.05],
        [-1.80, 0.05],   # adaptive hold (<=30)
        [0.35, 0.70],    # stage 2: wind-up
        [0.35, 1.10],    # tuck the elbow in the air
        [-1.80, 0.05],   # whip-slam (shoulder + elbow strike together)
        [-1.80, 0.05],   # adaptive press hold (<=40)
        [-1.80, 0.05],   # final hold (<=90)
        [0.0, 0.0],      # retract
    ],
    "pitch_pos": [
        [-1.32, 1.45],
        [-0.25, 1.45],
        [0.0, 0.0],
    ],
    "pitch_neg": [
        [-1.32, -1.65],
        [-0.25, -1.65],
        [0.0, 0.0],
    ],
}


def getup_sequence_for_pose(pose: str) -> np.ndarray:
    return np.asarray(SEQUENCES[pose], dtype=np.float64)
