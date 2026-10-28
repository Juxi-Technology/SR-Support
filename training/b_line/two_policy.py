"""Run a fall policy and switch to a learned arm-prop stand policy.

The fall policy (ppo_b39_rq) gets the body up to the stable arm-prop pose;
the stand policy (BC+PPO from the arm-prop) retracts both joints to vertical.
Used by play.py and the battery validation; the firmware mirrors this switch.
"""

from __future__ import annotations

import numpy as np

ARM_UP = 0.85
Q1_LO, Q1_HI = 1.20, 1.75
Q2_LO, Q2_HI = -0.10, 0.35
QUIET = 1.0
SWITCH_TICKS = 20
STAND_UP = 0.90
STAND_Q = 0.35
STAND_TICKS = 25
FALL_UP = 0.50

# Short-side stall pump (same envelope as the scripted routine).
LEFT_UP_LO, LEFT_UP_HI = 0.35, 0.75
LEFT_FLAT_LO = -0.20
SHOULDER_MIN = -1.07
PUMP_PERIOD, PUMP_MAX, PUMP_INVERT_TICKS = 20, 400, 20
PUMP_INVERT_UP = -0.45
PUMP_COOLDOWN = 75


class TwoPolicy:
    def __init__(self, fall_model, stand_model):
        self.fall = fall_model
        self.stand = stand_model
        self.state = "fall"
        self.k = 0
        self.hold = 0
        self.pump = 0
        self.inv = 0
        self.cooldown = 0

    def reset(self) -> None:
        self.state = "fall"
        self.k = 0
        self.hold = 0
        self.pump = 0
        self.inv = 0
        self.cooldown = 0

    def act(self, obs, env) -> np.ndarray:
        inner = env.unwrapped if hasattr(env, "unwrapped") else env
        up = float(inner._up_body()[2])
        q = np.asarray(inner._prev_cmd)
        w = float(np.linalg.norm(inner.data.qvel[3:6]))
        if self.state == "pump":
            cmd = q.copy()
            cmd[0] = SHOULDER_MIN
            goal = 1.55 if (self.pump // PUMP_PERIOD) % 2 == 0 else -1.55
            cmd[1] += float(np.clip(goal - cmd[1], -0.08, 0.08))
            inner.ctrl_override = cmd
            self.pump += 1
            if up < PUMP_INVERT_UP:
                self.inv += 1
            else:
                self.inv = 0
            if up > 0.90 or self.pump > PUMP_MAX or self.inv >= PUMP_INVERT_TICKS:
                self.state = "fall"
                self.cooldown = PUMP_COOLDOWN
                self.pump = 0
                self.inv = 0
            return np.zeros(2)
        if self.state == "fall":
            action, _ = self.fall.predict(obs, deterministic=True)
            if self.cooldown > 0:
                self.cooldown -= 1
                self.k = 0
            elif ((LEFT_UP_LO < up < LEFT_UP_HI)
                    or (LEFT_FLAT_LO < up < LEFT_UP_LO)):
                if q[0] < SHOULDER_MIN + 0.20 and w < QUIET:
                    self.k += 1
                    if self.k >= 10:
                        self.state = "pump"
                        self.pump = 0
                        self.inv = 0
                        self.k = 0
                else:
                    self.k = 0
            elif (up > ARM_UP and Q1_LO < q[0] < Q1_HI
                    and Q2_LO < q[1] < Q2_HI and w < QUIET):
                self.k += 1
                if self.k >= SWITCH_TICKS:
                    self.state = "stand"
                    self.k = 0
                    self.hold = 0
            else:
                self.k = 0
            return action
        action, _ = self.stand.predict(obs, deterministic=True)
        if up > STAND_UP and float(np.max(np.abs(q))) < STAND_Q:
            self.hold += 1
            if self.hold >= STAND_TICKS:
                self.state = "fall"
                self.hold = 0
        else:
            self.hold = 0
        if up < FALL_UP:
            self.state = "fall"
        return action
