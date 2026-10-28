"""Deterministic stand-homing controller for the final upright pose.

The RL policy is responsible for getting the robot off the ground. As soon as
the body is up (and has been stable for a short hold), this controller ramps
both joint targets to zero -- the assembly pose with the arm vertical -- at the
firmware's maximum slew rate. The lift pauses automatically whenever the body
tilts, and control returns to the policy if it falls.

States: policy -> home -> stand -> (policy if it falls).
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

from .selfright_env import ACTION_DELTA

Q_TOL = 0.02          # rad; below this the target snaps to zero


class StandHomer:
    def __init__(
        self,
        up: float = 0.95,
        omega: float = 1.5,
        quiet_steps: int = 10,
        rate: float = 0.12,
        pause: float = 0.95,
        fall: float = 0.90,
    ):
        self.up = up
        self.omega = omega
        self.quiet_steps = quiet_steps
        self.rate = rate
        self.pause_th = pause
        self.fall = fall
        self.state = "policy"
        self.quiet = 0
        self.pause = False

    def action(self, env) -> np.ndarray | None:
        """Action for this control step; None means 'let the policy act'."""
        if self.state == "policy":
            return None
        cmd = env._prev_cmd.copy()
        if not self.pause:
            cmd = cmd + np.clip(-cmd, -self.rate, self.rate)
        if float(np.max(np.abs(cmd))) < Q_TOL:
            cmd[:] = 0.0
            self.state = "stand"
        if getattr(env, "action_mode", "absolute") == "increment":
            return np.clip((cmd - env._prev_cmd) / ACTION_DELTA, -1.0, 1.0)
        return cmd / env.q_half

    def update(self, env, info: dict) -> None:
        """Update the state machine after env.step()."""
        if self.state == "policy":
            quiet = float(np.linalg.norm(env.data.qvel[3:6])) < self.omega
            if info["up_z"] > self.up and info["height_ok"] and quiet:
                self.quiet += 1
                if self.quiet >= self.quiet_steps:
                    self.state = "home"
                    self.pause = False
            else:
                self.quiet = 0
        elif self.state == "home":
            # Stop lifting while the body is still settling; resume when stable.
            self.pause = info["up_z"] < self.pause_th
            if info["up_z"] < self.fall:
                self.state = "policy"
                self.quiet = 0
        elif self.state == "stand":
            if info["up_z"] < self.fall:
                self.state = "policy"
                self.quiet = 0


class PushStand:
    """Push the arm past horizontal, then lift it out slowly to the stand pose.

    With the shoulder limited to +-1.55 rad the tall-riser build tops out
    leaning on the extended arm at ~23 deg: the arm tip is planted and the
    body is wedged. With a wide-range shoulder (+-2.0 rad) the arm keeps
    pushing the body upright, and a slow retract then brings it down onto the
    base in the arm-vertical pose.

    States: policy -> push -> hold -> retract -> stand (policy if it falls).
    The push/retract pair is a trajectory-search result from the arm-prop
    pose: shoulder 1.86 rad, elbow 0.83 rad, then a fast (0.033 rad/tick)
    retract to vertical; it stands in ~1.7 s with no arm-floor penetration.
    A left-lying stall (shoulder at its short-side limit) gets a left_pump
    phase first: elbow at its cap and oscillating, which rolls the body over;
    the policy then picks it up from the flipped pose.
    Only used when the robot spec allows targets beyond q_half (q_ctrl_max).
    """

    def __init__(
        self,
        up_lo: float = 0.6,
        arm_out: float = 0.5,
        quiet_steps: int = 20,
        push: float = 1.8628,
        push_rate: float = 0.0367,
        elbow_push: float = 0.8278,
        elbow_push_rate: float = 0.0367,
        hold_steps: int = 10,
        retract_rate: float = 0.0328,
        pause: float = 0.920,
        fall: float = 0.5,
        pump_amp: float = 0.4,
        pump_period: int = 20,
        pump_steps: int = 120,
        pump_full_steps: int = 400,
        pump_invert_up: float = -0.45,
        pump_invert_ticks: int = 20,
        pen_abort: float = 0.005,
        pen_abort_ticks: int = 5,
    ):
        self.up_lo = up_lo
        self.arm_out = arm_out
        self.quiet_steps = quiet_steps
        self.push = push
        self.push_rate = push_rate
        self.elbow_push = elbow_push
        self.elbow_push_rate = elbow_push_rate
        self.hold_steps = hold_steps
        self.retract_rate = retract_rate
        self.pause = pause
        self.fall = fall
        self.pump_amp = pump_amp
        self.pump_period = pump_period
        self.pump_steps = pump_steps
        self.pump_full_steps = pump_full_steps
        self.pump_invert_up = pump_invert_up
        self.pump_invert_ticks = pump_invert_ticks
        self.pen_abort = pen_abort
        self.pen_abort_ticks = pen_abort_ticks
        self.pump_mode = "wedge"
        self.state = "policy"
        self.k = 0
        self.sign = 1.0
        self.hold = 0
        self.stuck = 0
        self.pump = 0
        self.inv_ticks = 0
        self.pen_ticks = 0
        self.cooldown = 0   # survives reset(): settle guard after a pump

    def reset(self) -> None:
        self.state = "policy"
        self.k = 0
        self.hold = 0
        self.stuck = 0
        self.pump = 0
        self.inv_ticks = 0
        self.pen_ticks = 0

    @staticmethod
    def _up(env) -> float:
        return float(env._up_body()[2])

    def apply(self, env) -> bool:
        """Set env.ctrl_override and return True while the routine is active."""
        if self.state == "policy":
            return False
        up = self._up(env)
        if up < self.fall and self.state != "left_pump":
            self.reset()
            return False
        # Do not force the arm through the floor or the base: a deep contact
        # for a few ticks aborts the routine and hands back to the policy.
        pen = (float(env.arm_penetration())
               if hasattr(env, "arm_penetration") else 0.0)
        if pen < -self.pen_abort:
            self.pen_ticks += 1
            if self.pen_ticks >= self.pen_abort_ticks:
                self.reset()
                self.cooldown = 75
                return False
        else:
            self.pen_ticks = 0
        cmd = env._prev_cmd.copy()
        if self.state == "left_pump":
            # Roll the body over: shoulder parked at its short-side limit.
            # Wedge poses use a small cosine pump (the verified two-face
            # escape); flat-lying poses need the full elbow travel on a
            # square wave (rate limit leaves a fast cosine behind).
            cmd[0] = float(env.lim_lo[0])
            q2_hi = float(env.ovr_hi[1])   # mechanical elbow travel
            q2_lo = float(env.ovr_lo[1])
            goal = q2_hi if (self.pump // self.pump_period) % 2 == 0 else q2_lo
            cmd[1] += float(np.clip(goal - cmd[1], -0.08, 0.08))
            self.pump += 1
        elif self.state == "push":
            lo, hi = env.lim_lo[0], env.lim_hi[0]
            goal = float(np.clip(self.sign * self.push, lo, hi))
            goal_elbow = float(np.clip(self.elbow_push, env.ovr_lo[1], env.ovr_hi[1]))
            if (abs(goal - cmd[0]) < 1e-3 and abs(goal_elbow - cmd[1]) < 1e-3):
                if self.sign < 0 and self.sign * self.push < lo - 1e-3:
                    # The short side has no room to push; sweep the arm across
                    # to the long-travel side instead.
                    self.sign = 1.0
                else:
                    self.state = "hold"
                    self.hold = 0
            cmd[0] += float(np.clip(goal - cmd[0], -self.push_rate, self.push_rate))
            cmd[1] += float(np.clip(goal_elbow - cmd[1],
                                    -self.elbow_push_rate, self.elbow_push_rate))
        elif self.state == "hold":
            cmd[0] = self.sign * self.push
            cmd[1] = self.elbow_push
            self.hold += 1
            if self.hold >= self.hold_steps:
                self.state = "retract"
        elif self.state == "retract":
            if up >= self.pause:
                # Lift the arm out slowly.
                cmd = cmd + np.clip(-cmd, -self.retract_rate, self.retract_rate)
            else:
                # The body is sagging: push the arm back down a little to
                # re-plant it, then resume lifting. Keeps the retract usable
                # under servo/mass randomization.
                goal = self.sign * self.push
                cmd[0] += float(np.clip(goal - cmd[0], 0.0, 2.0 * self.retract_rate))
                cmd[1] += float(np.clip(self.elbow_push - cmd[1], 0.0,
                                        2.0 * self.retract_rate))
            if float(np.max(np.abs(cmd))) < 0.02:
                cmd[:] = 0.0
                self.state = "stand"
        else:  # stand
            cmd[:] = 0.0
        env.ctrl_override = cmd
        return True

    def update(self, env, info: dict) -> None:
        if self.state == "policy":
            up = float(info["up_z"])
            q1 = float(env._prev_cmd[0])
            quiet = float(np.linalg.norm(env.data.qvel[3:6])) < 1.0
            lo = float(env.lim_lo[0])
            if self.cooldown > 0:
                self.cooldown -= 1
                self.k = 0
            elif (0.35 < up < 0.75 or -0.2 < up < 0.35) and q1 < lo + 0.20 and quiet:
                # Wedged on the short-travel side: elbow-pump to roll over.
                self.k += 1
                if self.k >= max(self.quiet_steps // 2, 1):
                    self.state = "left_pump"
                    self.pump_mode = "flat" if up < 0.35 else "wedge"
                    self.pump = 0
                    self.k = 0
            elif up >= self.up_lo and abs(q1) > self.arm_out and quiet:
                # Body up (or at the old arm-prop lean) with the arm still out:
                # re-plant the arm fully first — the extra push lifts the body and
                # gives the lift-out room to work — then hold and retract.
                self.k += 1
                if self.k >= self.quiet_steps:
                    self.state = "push"
                    self.sign = 1.0 if q1 > 0 else -1.0
                    self.k = 0
            else:
                self.k = 0
        elif self.state == "left_pump":
            # A momentary roll past horizontal is the pump working, but a
            # settled inverted pose is not: stop after a short confirmation
            # and let the policy flip the body instead of pumping for 8 s.
            up = float(info["up_z"])
            if up < self.pump_invert_up:
                self.inv_ticks += 1
            else:
                self.inv_ticks = 0
            if (up > 0.9 or self.pump > self.pump_full_steps
                    or self.inv_ticks >= self.pump_invert_ticks):
                self.reset()
                self.cooldown = 75   # let the policy settle before re-pumping
        elif self.state == "stand":
            if float(info["up_z"]) < 0.9:
                self.reset()


class FallGate:
    """Mirror the firmware's get-up gate: hold the arm until fully fallen.

    The policy may only act after the body has been below up_z=0.35 with a
    quiet body rate for 10 control ticks; it is disarmed again once the robot
    has stood quietly for 25 ticks. Without this gate the policy reacts during
    a push, drives the arm to its long-side limit, and the robot lands fully
    inverted in a pose the policy cannot leave.
    """

    def __init__(
        self,
        up_fall: float = 0.35,
        omega: float = 1.5,
        fall_steps: int = 10,
        up_stand: float = 0.95,
        stand_steps: int = 25,
        q_stand: float = 0.20,
    ):
        self.up_fall = up_fall
        self.omega = omega
        self.fall_steps = fall_steps
        self.up_stand = up_stand
        self.stand_steps = stand_steps
        self.q_stand = q_stand
        self.armed = False
        self.fall_k = 0
        self.stand_k = 0

    def update(self, env, info: dict, state: str | None = None) -> None:
        inner = env.unwrapped if hasattr(env, "unwrapped") else env
        quiet = float(np.linalg.norm(inner.data.qvel[3:6])) < self.omega
        if not self.armed:
            if info["up_z"] < self.up_fall and quiet:
                self.fall_k += 1
                if self.fall_k >= self.fall_steps:
                    self.armed = True
                    self.fall_k = 0
            else:
                self.fall_k = 0
        else:
            # Do not disarm while a stand routine is still moving the arm.
            active = state in ("push", "hold", "retract", "home", "left_pump")
            settled = float(np.max(np.abs(inner._prev_cmd))) < self.q_stand
            if (not active and info["up_z"] > self.up_stand and quiet
                    and settled):
                self.stand_k += 1
                if self.stand_k >= self.stand_steps:
                    self.armed = False
                    self.stand_k = 0
            else:
                self.stand_k = 0


class HomerWrapper(gym.Wrapper):
    """Let a stand controller act inside training, as the firmware does.

    The policy still has to get the body up; once it is upright and quiet the
    homer takes over and ramps the arm to the vertical pose. On a wide-range
    shoulder the push-stand routine is used instead: it pushes the arm past
    the arm-prop wedge first, then lifts out slowly.
    """

    def __init__(self, env: gym.Env, fall_gate: bool = False):
        super().__init__(env)
        self._fall_gate = fall_gate
        self.gate = FallGate() if fall_gate else None
        self.homer = self._make()

    def _make(self):
        inner = self.env.unwrapped if hasattr(self.env, "unwrapped") else self.env
        if getattr(inner, "q_ctrl_max", inner.q_half) > inner.q_half + 1e-6:
            return PushStand()
        return StandHomer()

    def reset(self, **kwargs):
        self.homer = self._make()
        self.gate = FallGate() if self._fall_gate else None
        return self.env.reset(**kwargs)

    def step(self, action):
        h = self.homer
        inner = self.env.unwrapped if hasattr(self.env, "unwrapped") else self.env
        gated = self.gate is not None and not self.gate.armed
        if gated:
            # Firmware parity: no policy or routine output until fully fallen.
            action = (np.zeros(2, dtype=np.float64)
                      if getattr(inner, "action_mode", "absolute") == "increment"
                      else inner._prev_cmd / inner.q_half)
        elif isinstance(h, PushStand):
            if h.apply(self.env):
                action = np.zeros(2, dtype=np.float64)
        elif h.state != "policy":
            action = h.action(self.env)
        obs, rew, terminated, truncated, info = self.env.step(action)
        if self.gate is not None:
            self.gate.update(self.env, info, h.state)
        if not gated:
            h.update(self.env, info)
        return obs, rew, terminated, truncated, info
