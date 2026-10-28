#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent Gymnasium environment for SR-Support 2-DOF slow getup.

This is an original implementation. It does not copy the environment, reward,
observation layout, or model of SelfRisingRobot (which has no license).

Observation (6):
    [roll_acc, pitch_acc, shoulder_angle, elbow_angle, shoulder_vel, elbow_vel]

    roll_acc/pitch_acc are computed by projecting gravity into the body frame,
    approximating the firmware's accelerometer-derived rollAcc/pitchAcc. This is
    closer to the real IMU than raw quaternion Euler angles and avoids the >90°
    gimbal-lock issue.

Action (2):
    target-angle deltas in [-1, 1], scaled by 0.08 rad per 20 ms control step.
    The internal target is clamped to +/-1.55 rad.

The MJCF in assets/sr_2dof.xml is a template; replace dimensions/masses with
your own CAD/BOM before expecting sim-to-real transfer.
"""

from __future__ import annotations

import math
from pathlib import Path

import gymnasium as gym
import numpy as np
from gymnasium import spaces

try:
    import mujoco
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "MuJoCo is required. Install with: pip install -r training/requirements.txt"
    ) from exc

MODEL_PATH = Path(__file__).resolve().parent / "assets" / "sr_2dof.xml"
CONTROL_DT = 0.02
ACTION_SCALE = 0.08
TARGET_LIMIT = 1.55
UPRIGHT_TILT = 0.25
FALLEN_TILT = 1.1


class Sr2DofEnv(gym.Env):
    """A small 2-DOF arm attached to a free-floating box."""

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "render_fps": 50,
    }

    def __init__(self, render_mode=None, randomize=True, max_seconds=14.0):
        super().__init__()
        if render_mode not in (None, "human", "rgb_array"):
            raise ValueError(f"unsupported render_mode: {render_mode}")

        self.model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
        self.data = mujoco.MjData(self.model)
        self.render_mode = render_mode
        self.randomize = randomize

        self.frame_skip = max(1, int(round(CONTROL_DT / self.model.opt.timestep)))
        self.max_steps = int(round(max_seconds / CONTROL_DT))

        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(2,), dtype=np.float32
        )
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(6,), dtype=np.float32
        )

        self._target = np.zeros(2, dtype=np.float64)
        self._prev_action = np.zeros(2, dtype=np.float32)
        self._step_count = 0
        self._upright_count = 0
        self._viewer = None
        self._renderer = None

    # ------------------------------------------------------------------
    # Gym API
    # ------------------------------------------------------------------
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        if self.randomize:
            # Mostly fallen poses, occasionally near-upright.
            if self.np_random.random() < 0.15:
                roll = self.np_random.uniform(-0.4, 0.4)
                pitch = self.np_random.uniform(-0.4, 0.4)
            else:
                primary_roll = self.np_random.random() < 0.5
                if primary_roll:
                    roll = self.np_random.choice([-1.0, 1.0]) * self.np_random.uniform(
                        FALLEN_TILT, 1.9
                    )
                    pitch = self.np_random.uniform(-0.5, 0.5)
                else:
                    roll = self.np_random.uniform(-0.5, 0.5)
                    pitch = self.np_random.choice([-1.0, 1.0]) * self.np_random.uniform(
                        FALLEN_TILT, 1.9
                    )
            yaw = self.np_random.uniform(-math.pi, math.pi)
            s1 = self.np_random.uniform(-1.2, 1.2)
            s2 = self.np_random.uniform(-1.2, 1.2)
        else:
            roll = math.pi / 2
            pitch = 0.0
            yaw = 0.0
            s1 = 0.8
            s2 = -0.8

        quat = np.zeros(4, dtype=np.float64)
        mujoco.mju_euler2Quat(
            quat,
            np.array([roll, pitch, yaw], dtype=np.float64),
            "xyz",
        )

        self.data.qpos[:] = 0.0
        self.data.qpos[0:3] = [0.0, 0.0, 0.16]
        self.data.qpos[3:7] = quat
        self.data.qpos[7] = s1
        self.data.qpos[8] = s2
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = [s1, s2]
        mujoco.mj_forward(self.model, self.data)

        # Let contacts settle briefly so the episode does not start in deep
        # penetration. This is not counted as part of the control episode.
        for _ in range(20):
            mujoco.mj_step(self.model, self.data)

        self._target = np.array(
            [self.data.qpos[7], self.data.qpos[8]], dtype=np.float64
        )
        self.data.ctrl[:] = self._target
        self._prev_action[:] = 0.0
        self._step_count = 0
        self._upright_count = 0
        return self._get_obs(), self._get_info()

    def step(self, action):
        action = np.asarray(action, dtype=np.float32).reshape(2)
        action = np.clip(action, -1.0, 1.0)

        self._target = np.clip(
            self._target + action * ACTION_SCALE, -TARGET_LIMIT, TARGET_LIMIT
        )
        self.data.ctrl[:] = self._target

        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)

        self._step_count += 1
        obs = self._get_obs()
        tilt = self._tilt()
        upright = tilt < UPRIGHT_TILT

        if upright:
            self._upright_count += 1
        else:
            self._upright_count = 0

        terminated = self._upright_count >= 25  # 0.5 s upright
        truncated = self._step_count >= self.max_steps

        reward = self._reward(action, tilt, upright)
        info = self._get_info()
        info["target"] = self._target.copy()
        info["action"] = action.copy()
        self._prev_action = action.copy()

        return obs, float(reward), bool(terminated), bool(truncated), info

    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                import mujoco.viewer

                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()
        elif self.render_mode == "rgb_array":
            if self._renderer is None:
                self._renderer = mujoco.Renderer(self.model, height=480, width=640)
            self._renderer.update_scene(self.data)
            return self._renderer.render()
        return None

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_obs(self) -> np.ndarray:
        roll, pitch = self._accel_roll_pitch()
        s1, s2 = self.data.qpos[7], self.data.qpos[8]
        v1, v2 = self.data.qvel[6], self.data.qvel[7]
        return np.array([roll, pitch, s1, s2, v1, v2], dtype=np.float32)

    def _get_info(self) -> dict:
        tilt = self._tilt()
        return {
            "tilt": float(tilt),
            "upright": bool(tilt < UPRIGHT_TILT),
            "step": int(self._step_count),
        }

    def _tilt(self) -> float:
        """Angle between body local +Z and world +Z, in radians."""
        mat = np.zeros(9, dtype=np.float64)
        mujoco.mju_quat2Mat(mat, self.data.qpos[3:7])
        # Row-major rotation matrix; element [2,2] is local +Z dot world +Z.
        return float(math.acos(float(np.clip(mat[8], -1.0, 1.0))))

    def _accel_roll_pitch(self) -> tuple[float, float]:
        """Approximate the firmware's accelerometer-derived roll/pitch.

        At rest the accelerometer measures the gravity reaction. In the body
        frame that is R^T * [0, 0, 1] (for a level, upright body it reads +1g
        on local Z). This mirrors the firmware formulas:
            rollAcc = atan2(ay, az)
            pitchAcc = atan2(-ax, sqrt(ay^2 + az^2))
        """
        mat = np.zeros(9, dtype=np.float64)
        mujoco.mju_quat2Mat(mat, self.data.qpos[3:7])
        rot = mat.reshape(3, 3)
        a_body = rot.T @ np.array([0.0, 0.0, 1.0], dtype=np.float64)
        roll = math.atan2(float(a_body[1]), float(a_body[2]))
        pitch = math.atan2(
            -float(a_body[0]),
            math.sqrt(float(a_body[1] ** 2 + a_body[2] ** 2)),
        )
        return roll, pitch

    @staticmethod
    def _quat_to_roll_pitch(quat) -> tuple[float, float]:
        # Kept for debugging/visualization; observation uses _accel_roll_pitch.
        w, x, y, z = [float(v) for v in quat]
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1.0:
            pitch = math.copysign(math.pi / 2.0, sinp)
        else:
            pitch = math.asin(sinp)
        return roll, pitch

    def _reward(self, action, tilt, upright) -> float:
        upright_reward = math.exp(-4.0 * tilt * tilt)
        height_reward = 0.2 * float(np.clip(self.data.qpos[2], 0.0, 0.2))
        action_cost = 0.01 * float(np.sum(action * action))
        velocity_cost = 0.001 * float(np.sum(self.data.qvel[6:8] ** 2))
        smooth_cost = 0.005 * float(np.sum((action - self._prev_action) ** 2))

        reward = upright_reward + height_reward - action_cost - velocity_cost - smooth_cost
        if upright:
            reward += 0.2
        if self._upright_count >= 25:
            reward += 5.0
        return float(reward)
