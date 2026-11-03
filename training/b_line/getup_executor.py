"""Deterministic reference + feedback get-up executor.

The searched waypoint sequences are the feed-forward target schedule (20
control ticks per waypoint, as in the reference search). The feedback is on
the body attitude:
  - the final phase retracts the arm to neutral at a constant rate; the
    retract is itself a lift in several poses, so it runs unconditionally;
  - if the body rolls onto a different lying axis while the current
    reference runs (the roll references yaw the body onto the pitch axis by
    dragging the forearm on the floor), the executor re-plans to the
    reference of the new pose instead of running the wrong sequence to the
    timeout, retracting to neutral first.

Everything here is scalar arithmetic on [up_x, up_y, up_z, q1_target,
q2_target], so the same code/constants can be implemented 1:1 in the ESP32
firmware.
"""

from __future__ import annotations

import numpy as np

from .getup_reference_b39 import getup_sequence_for_pose

# Firmware parity (firmware/sr_support_b_ptk/src/main.cpp EXEC_R1_HOLD): a
# capped phase holds its target while the body is still down (up_z below
# HOLD_UP) and advances once it comes up or when the cap expires, so a
# stalled mechanism hands over to the next one. The executor also exits
# straight to the retract when the body gets upright mid-sequence.
HOLD_UP = 0.92
HOLD_TICKS = {
    "roll_neg": [0, 0, 0, 50, 0, 40, 0, 0, 40, 0, 0, 100, 0],
}


class GetupExecutor:
    def __init__(
        self,
        pose: str,
        steps_per_wp: int = 20,
        retract_rate: float = 0.033,
        pause_up: float = 0.95,
        support_scale: float = 1.0,
        switch_ticks: int = 15,
        switch_up: float = 0.60,
        switch_w: float = 0.8,
        min_switch_age: int = 25,
        max_switches: int = 5,
        neutral_max: int = 120,
        q0=None,
    ):
        self.steps_per_wp = int(steps_per_wp)
        self.retract_rate = float(retract_rate)
        self.pause_up = float(pause_up)
        self.support_scale = float(support_scale)
        self.switch_ticks = int(switch_ticks)
        self.switch_up = float(switch_up)
        self.switch_w = float(switch_w)
        self.min_switch_age = int(min_switch_age)
        self.max_switches = int(max_switches)
        self.neutral_max = int(neutral_max)
        self.switches = 0
        self.other_ticks = 0
        self.age = 0
        self.neutral = False
        self.neutral_ticks = 0
        self.pending_pose = None
        self.retract_up0 = None
        self.retract_ok = True
        self._load(pose, q0)

    def _load(self, pose, q):
        """(Re)start the reference for `pose` from the current target `q`."""
        self.sequence = np.asarray(getup_sequence_for_pose(pose), dtype=np.float64)
        self.hold = HOLD_TICKS.get(pose, [])
        self.pose = pose
        self.support = (self.sequence[-2] * self.support_scale
                        if len(self.sequence) > 1 else np.zeros(2))
        self.phase = 0
        self.tick = 0
        self.other_ticks = 0
        self.age = 0
        self.retract_up0 = None
        self.retract_ok = True
        self.prev = np.zeros(2) if q is None else np.asarray(q, dtype=np.float64).copy()
        self.target = self.prev.copy()

    def _maybe_switch(self, q, up_x, up_y, up_z, w):
        if self.neutral or self.age < self.min_switch_age:
            self.other_ticks = 0
            return
        if (up_z >= self.switch_up or w >= self.switch_w
                or self.switches >= self.max_switches):
            self.other_ticks = 0
            return
        candidate = pose_from_up(up_x, up_y)
        if candidate == self.pose:
            self.other_ticks = 0
            return
        self.other_ticks += 1
        if self.other_ticks >= self.switch_ticks:
            self.switches += 1
            self.other_ticks = 0
            self.neutral = True
            self.neutral_ticks = 0
            self.pending_pose = candidate

    def _neutral_target(self, q):
        """Retract both joints to the neutral pose before the next reference."""
        cmd = q + np.clip(-q, -self.retract_rate, self.retract_rate)
        self.neutral_ticks += 1
        if float(np.max(np.abs(q))) < 0.02 or self.neutral_ticks > self.neutral_max:
            cmd = np.zeros(2)
            self.neutral = False
            self._load(self.pending_pose, np.zeros(2))
        self.target = cmd
        return cmd

    def action(self, env, obs=None) -> np.ndarray:
        q = np.asarray(env.target, dtype=np.float64)
        up_vec = env.data.xmat[env.foot_body_id].reshape(3, 3)[2]
        w = float(np.linalg.norm(env.data.qvel[3:6]))
        self.age += 1
        self._maybe_switch(q, float(up_vec[0]), float(up_vec[1]),
                           float(up_vec[2]), w)
        if self.neutral:
            cmd = self._neutral_target(q)
            return np.clip((cmd - q) / env.target_delta, -1.0, 1.0).astype(np.float32)
        up = float(up_vec[2])
        if (self.hold and up > HOLD_UP
                and self.phase < len(self.sequence) - 1):
            self.phase = len(self.sequence) - 1
            self.tick = 0
        if self.phase < len(self.sequence) - 1:
            wp = self.sequence[self.phase]
            self.tick += 1
            frac = min(self.tick / max(self.steps_per_wp, 1), 1.0)
            cmd = (1.0 - frac) * self.prev + frac * wp
            if self.tick >= self.steps_per_wp:
                cap = (self.hold[self.phase]
                       if self.phase < len(self.hold) else 0)
                if cap and up < HOLD_UP and self.tick < cap:
                    pass  # hold until the body comes up or the cap expires
                else:
                    self.prev = wp
                    self.phase += 1
                    self.tick = 0
        else:
            # Final phase: retract the arm to neutral at a constant rate. The
            # retract is itself a lift in several poses (the arm pushes the
            # body while folding), so it runs unconditionally; a topple is
            # handled by the pose re-plan / fall gate above.
            cmd = q + np.clip(-q, -self.retract_rate, self.retract_rate)
            if float(np.max(np.abs(q))) < 0.02:
                cmd = np.zeros(2)
        self.target = cmd
        return np.clip((cmd - q) / env.target_delta, -1.0, 1.0).astype(np.float32)


def pose_from_attitude(roll: float, pitch: float) -> str:
    if abs(roll) >= abs(pitch):
        return "roll_pos" if roll >= 0.0 else "roll_neg"
    return "pitch_pos" if pitch >= 0.0 else "pitch_neg"


def pose_from_up(up_x: float, up_y: float) -> str:
    """Classify the fall from the body-frame up vector (no Euler gimbal)."""
    if abs(up_x) >= abs(up_y):
        return "pitch_pos" if up_x < 0.0 else "pitch_neg"
    return "roll_pos" if up_y > 0.0 else "roll_neg"
