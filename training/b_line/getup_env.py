"""Reference-guided get-up environment for the 4 cm b39 build.

Mirrors the original SelfRisingRobot pipeline (robo1_env.py): 4 canonical
fallen poses, observation [roll, pitch, target1, target2], action = target
increments of 0.08 rad, target limits = the mechanical joint range. The
scripted reference sequences are searched separately (search_b39_getup.py),
then used to pretrain a policy (BC) and fine-tune with PPO.
"""

from __future__ import annotations

import math
from pathlib import Path

import gymnasium as gym
import mujoco
import numpy as np
from gymnasium import spaces

XML = Path(__file__).resolve().parents[2] / "hardware" / "v1" / "robot_v1.xml"

FALLEN_POSES = {
    "roll_pos": (math.pi / 2.0, 0.0),
    "roll_neg": (-math.pi / 2.0, 0.0),
    "pitch_pos": (0.0, math.pi / 2.0),
    "pitch_neg": (0.0, -math.pi / 2.0),
}
DEFAULT_FALLEN_POSES = tuple(FALLEN_POSES)

# Mechanical command range of the re-indexed 180 deg shoulder and elbow.
Q_LO = np.array([-1.07, -1.55], dtype=np.float64)
Q_HI = np.array([2.07, 1.55], dtype=np.float64)

# Initial servo-joint velocities (rad/s: shoulder, elbow) applied when the
# limp settle starts. On the real robot the arm carries momentum from the
# fall; without it the released arm can balance on the base rim instead of
# falling to the floor. Sign = the open side of each pose (away from the
# base), so the arm tip lands on the open floor.
LIMP_KICK = {
    "roll_pos": (1.0, 0.0),
    "roll_neg": (-1.0, 0.0),
    "pitch_pos": (0.0, 1.0),
    "pitch_neg": (0.0, -1.0),
}
LIMP_SETTLE_TIME = 2.0  # s, released-servo settle (the fall is slow)


def roll_pitch_to_quat(roll, pitch):
    cr = math.cos(roll / 2.0)
    sr = math.sin(roll / 2.0)
    cp = math.cos(pitch / 2.0)
    sp = math.sin(pitch / 2.0)
    return np.array([cr * cp, sr * cp, cr * sp, -sr * sp], dtype=np.float64)


def quat_to_roll_pitch(q):
    w, x, y, z = q
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2.0 * (w * y - z * x)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.asin(sinp)
    return roll, pitch


class B39GetupEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, fallen_poses=None, max_steps: int = 700,
                 settle_time: float = 0.4, xml_path=None,
                 limp_settle: bool = False):
        super().__init__()
        xml = Path(xml_path) if xml_path is not None else XML
        self.model = mujoco.MjModel.from_xml_path(str(xml))
        self.data = mujoco.MjData(self.model)
        # limp_settle: release the servos (zero torque: ctrl tracks the joint
        # position) while the fallen pose settles, so gravity decides the
        # resting arm pose - the arm falls until it touches the floor, as on
        # the passive robot. The servos then re-engage at the settled angles.
        self.limp_settle = bool(limp_settle)

        self.phys_dt = float(self.model.opt.timestep)
        self.frame_skip = max(1, int(round(0.02 / self.phys_dt)))
        self.settle_steps = max(1, int(round(settle_time / self.phys_dt)))
        self.max_steps = max_steps
        self.target_delta = 0.08

        self.fallen_poses = list(fallen_poses or DEFAULT_FALLEN_POSES)
        self.current_pose_name = self.fallen_poses[0]

        self.foot_body_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_BODY, "foot")
        self.root_jid = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_JOINT, "root")
        self.servo_jids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "servo1_joint"),
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "servo2_joint"),
        ]
        self.qpos_adr = [int(self.model.jnt_qposadr[j]) for j in self.servo_jids]
        self.qvel_adr = [int(self.model.jnt_dofadr[j]) for j in self.servo_jids]
        self.arm_bids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "arm1"),
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "arm2"),
        ]
        self.standing_height = self._compute_standing_height()

        self.action_space = spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=np.array([-math.pi, -math.pi, Q_LO[0], Q_LO[1]], dtype=np.float32),
            high=np.array([math.pi, math.pi, Q_HI[0], Q_HI[1]], dtype=np.float32),
            dtype=np.float32,
        )

        self.step_count = 0
        self.target = np.zeros(2, dtype=np.float64)
        self.success_count = 0
        self.prev_upright = 0.0

    def _compute_standing_height(self):
        d = mujoco.MjData(self.model)
        d.qpos[:] = 0.0
        d.qpos[0:3] = [0.0, 0.0, 0.08]
        d.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]
        d.ctrl[:] = 0.0
        mujoco.mj_forward(self.model, d)
        for _ in range(self.settle_steps):
            d.ctrl[:] = 0.0
            mujoco.mj_step(self.model, d)
        return float(d.xpos[self.foot_body_id, 2])

    def arm_penetration(self) -> float:
        m, d = self.model, self.data
        arm = [b for b in self.arm_bids if b >= 0]
        worst = 0.0
        for i in range(d.ncon):
            c = d.contact[i]
            b1 = int(m.geom_bodyid[c.geom1])
            b2 = int(m.geom_bodyid[c.geom2])
            if ((b1 in arm and b2 in (self.foot_body_id, 0))
                    or (b2 in arm and b1 in (self.foot_body_id, 0))):
                worst = min(worst, float(c.dist))
        return worst

    def _obs(self):
        roll, pitch = quat_to_roll_pitch(self.data.qpos[3:7])
        return np.array([roll, pitch, self.target[0], self.target[1]],
                        dtype=np.float32)

    def _upright(self):
        return float(self.data.xmat[self.foot_body_id].reshape(3, 3)[2, 2])

    def _foot_height(self):
        return float(self.data.xpos[self.foot_body_id, 2])

    def _servo_angles(self):
        return np.array([self.data.qpos[a] for a in self.qpos_adr], dtype=np.float64)

    def _servo_velocities(self):
        return np.array([self.data.qvel[a] for a in self.qvel_adr], dtype=np.float64)

    def _set_pose(self, pose_name):
        self.data.qpos[:] = 0.0
        self.data.qvel[:] = 0.0
        self.data.qpos[0:3] = [0.0, 0.0, 0.08]
        roll, pitch = FALLEN_POSES[pose_name]
        self.data.qpos[3:7] = roll_pitch_to_quat(roll, pitch)
        if self.limp_settle:
            # the arm keeps a little momentum from the fall so it topples off
            # the base rim instead of balancing on it (direction: away from
            # the base, per pose)
            self.data.qvel[self.qvel_adr[0]] = LIMP_KICK.get(pose_name, (0.0, 0.0))[0]
            self.data.qvel[self.qvel_adr[1]] = LIMP_KICK.get(pose_name, (0.0, 0.0))[1]
        self.target[:] = 0.0
        self.data.ctrl[:] = self.target
        mujoco.mj_forward(self.model, self.data)
        if self.limp_settle:
            # Zero the actuator gains so the servos are truly limp for the
            # settle (a ctrl-tracks-qpos servo still adds kp*dt+kv of viscous
            # damping and freezes the arm mid-air). Restored afterwards.
            gain = self.model.actuator_gainprm.copy()
            bias = self.model.actuator_biasprm.copy()
            self.model.actuator_gainprm[:] = 0.0
            self.model.actuator_biasprm[:] = 0.0
            limp_steps = max(1, int(round(LIMP_SETTLE_TIME / self.phys_dt)))
            for _ in range(limp_steps):
                mujoco.mj_step(self.model, self.data)
            self.model.actuator_gainprm[:] = gain
            self.model.actuator_biasprm[:] = bias
            # engage the servos at the settled pose (no target jump)
            self.target[:] = np.clip(self.data.qpos[self.qpos_adr], Q_LO, Q_HI)
            self.data.ctrl[:] = self.target
            for _ in range(self.settle_steps):
                self.data.ctrl[:] = self.target
                mujoco.mj_step(self.model, self.data)
            self.target[:] = np.clip(self.data.qpos[self.qpos_adr], Q_LO, Q_HI)
        else:
            for _ in range(self.settle_steps):
                self.data.ctrl[:] = self.target
                mujoco.mj_step(self.model, self.data)
            self.target[:] = 0.0
            self.data.ctrl[:] = self.target
        self.current_pose_name = pose_name

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0
        self.success_count = 0
        pose_name = None
        if options is not None:
            pose_name = options.get("pose")
        if pose_name is None:
            pose_name = self.np_random.choice(self.fallen_poses)
        self._set_pose(pose_name)
        self.prev_upright = self._upright()
        return self._obs(), {"pose": self.current_pose_name}

    def step(self, action):
        action = np.clip(np.asarray(action, dtype=np.float64), -1.0, 1.0)
        old_target = self.target.copy()
        self.target = np.clip(self.target + action * self.target_delta, Q_LO, Q_HI)
        for _ in range(self.frame_skip):
            self.data.ctrl[:] = self.target
            mujoco.mj_step(self.model, self.data)

        self.step_count += 1
        obs = self._obs()
        upright = self._upright()
        upright_progress = upright - self.prev_upright
        self.prev_upright = upright
        roll, pitch = float(obs[0]), float(obs[1])
        servo_angles = self._servo_angles()
        servo_velocities = self._servo_velocities()
        foot_height_error = self._foot_height() - self.standing_height
        pen = self.arm_penetration()

        tilt_cost = 0.2 * (roll * roll + pitch * pitch)
        stand_gate = float(np.clip((upright - 0.65) / 0.35, 0.0, 1.0))
        reward = (
            2.0 * upright
            + 8.0 * upright_progress
            - tilt_cost
            - stand_gate * 0.5 * float(np.sum(servo_angles * servo_angles))
            - stand_gate * 0.2 * float(np.sum(self.target * self.target))
            - stand_gate * 5.0 * foot_height_error * foot_height_error
            - 0.01 * float(np.sum(self.data.qvel[0:6] * self.data.qvel[0:6]))
            - 0.005 * float(np.sum(servo_velocities * servo_velocities))
            - 0.005 * float(np.sum(action * action))
            - 0.02 * float(np.sum((self.target - old_target) ** 2))
            - 20.0 * max(0.0, -pen - 0.005)
        )

        goal_pose = (
            upright > 0.95
            and abs(roll) < 0.25
            and abs(pitch) < 0.25
            and np.max(np.abs(servo_angles)) < 0.12
            and abs(foot_height_error) < 0.02
            and np.linalg.norm(self.data.qvel[0:6]) < 0.25
        )
        if goal_pose:
            self.success_count += 1
            reward += 5.0
        else:
            self.success_count = 0
        terminated = self.success_count >= 50
        truncated = self.step_count >= self.max_steps
        info = {
            "pose": self.current_pose_name,
            "upright": upright,
            "foot_height_error": foot_height_error,
            "servo_angles": servo_angles.copy(),
            "goal_pose": goal_pose,
            "target": self.target.copy(),
            "success_count": self.success_count,
            "pen": pen,
        }
        return obs, float(reward), terminated, truncated, info
