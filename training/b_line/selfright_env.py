"""Gymnasium environment: SR-Support self-righting robot (2x PTK7452MG).

Based on Juxi-Technology/2dof-selfrighting-robot sim/selfright_env.py
(MIT/Apache-2.0); see third_party/juxi-2dof/. Local changes:
  - default model is the user's SelfRisingRobot 3D print
    (training/b_line/assets/robot_selfrising.xml, built from the STL parts)
  - Juxi B-line geometry is kept as the "ptk7452" model for comparison
  - torque limit is 3.4 kg*cm at 6 V (0.333 N*m)
  - per-robot body name and contact geoms

Coordinate conventions (must match the firmware):
  body frame: x forward, y left, z up.
  up_b = world up expressed in the body frame. Upright => up_b = (0, 0, 1).
  omega = body-frame angular velocity, rad/s.
  q = 0 is the arm's mechanical neutral.

Policy I/O (dim 10 -> dim 2), 50 Hz:
  obs = [up_b(3), omega(3), q(2), qdot(2)]
  action in [-1, 1]^2 -> target joint angle a * q_half

PTK7452MG has no position feedback, so q/qdot are the commanded angle/rate.
"""

from __future__ import annotations

from pathlib import Path

import gymnasium as gym
import mujoco
import numpy as np
from gymnasium import spaces

CTRL_DT = 0.02            # policy / servo command period, s (50 Hz)
SETTLE_TIME = 0.4         # s of settling before the policy starts
EPISODE_STEPS = 400       # 8 s
MAX_CMD_RATE = 0.12       # rad per control step (absolute-action slew limit)
ACTION_DELTA = 0.08       # rad per control step (increment-action mode)
MAX_DELAY_STEPS = 5       # command latency up to 5 control steps (100 ms)
OBS_DELAY_STEPS = 2       # IMU/attitude observation lag up to 2 steps (40 ms)

OBS_DIM = 10
ACT_DIM = 2

UP_STAND = 0.90           # up_b[2] above this = body base down (upright)
HEIGHT_TOL = 0.03         # torso height within this of the standing height
Q_STAND_TOL = 0.35        # max |q| (rad) for the settled, arm-vertical stand pose

# Four canonical fallen poses of the 2R arm robot (roll/pitch about body x/y).
POSE_RP = {
    "roll_pos": (np.pi / 2.0, 0.0),
    "roll_neg": (-np.pi / 2.0, 0.0),
    "pitch_pos": (0.0, np.pi / 2.0),
    "pitch_neg": (0.0, -np.pi / 2.0),
}

ROBOT_SPECS = {
    # SR-Support: the user's SelfRisingRobot 3D print, 2x PTK7452MG.
    # Geometry built from the actual STLs; masses per tools/build_selfrising_model.py.
    "selfrising": {
        "xml": "assets/robot_selfrising.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar"],
        "description": "SelfRisingRobot 3D print + 2x PTK7452MG (3.4 kg*cm @6V)",
    },
    # User's actual bulky build: base riser +6 cm and arm2 +6 cm.
    "r60l6_sr5": {
        "xml": "assets/robot_selfrising_riser60_long6.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        # Extra time: this geometry needs a long rock-up before it can tip
        # the base flat; 8 s episodes end while it is still propped on the arm.
        "episode_steps": 600,
        "description": "base +6 cm, arm +6 cm, SR interface",
    },
    # Same bulky build with the user's real base footprint (8.5x8.5 cm).
    "r60l6b85_sr5": {
        "xml": "assets/robot_selfrising_r60l6_b85.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "base +6 cm on an 8.5x8.5 cm footprint, arm +6 cm, SR interface",
    },
    # 8.5x8.5 base plus a ~10 g rear counterweight (foot COM y: -10.4 -> 0 mm).
    "r60l6b85cg_sr5": {
        "xml": "assets/robot_selfrising_r60l6_b85cg.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "8.5x8.5 base, rear counterweight, arm +6 cm, SR interface",
    },
    # 8.5 x 10.5 cm base (+2 cm depth): smallest footprint where the body
    # settles onto the base instead of getting wedged on the extended arm.
    "r60l6b85x105_sr5": {
        "xml": "assets/robot_selfrising_r60l6_b85x105.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "8.5x10.5 base, arm +6 cm, SR interface",
    },
    # User's measured build: 8.5x8.5 base and 26 cm from the base top face to
    # the arm top when standing (arm2 extension 9.2 cm, not 6 cm).
    "r60l6h26_sr5": {
        "xml": "assets/robot_selfrising_r60l6_h26.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "8.5x8.5 base, 26 cm overall arm height, SR interface",
    },
    # Same build with a wide-range shoulder servo (+-2.0 rad travel): the arm
    # can push past horizontal to lift the body out of the arm-prop wedge.
    "r60l6h26r20_sr5": {
        "xml": "assets/robot_selfrising_r60l6_h26_r20.xml",
        "q_half": 1.55,
        "q_ctrl_max": 2.0,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "8.5x8.5 base, 26 cm arm, shoulder range +-115 deg",
    },
    # Same build, 180 deg servo kept: arm horn re-indexed 2 teeth (~28.8 deg),
    # shoulder travel [-1.07, +2.07] rad. Push-stand needs the + side.
    "r60l6h26ri_sr5": {
        "xml": "assets/robot_selfrising_r60l6_h26_ri.xml",
        "q_half": 1.55,
        "q_min": -1.07,
        "q_max": 2.07,
        "q_ctrl_max": 2.07,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "8.5x8.5 base, 26 cm arm, re-indexed horn (180 deg servo)",
    },
    # Base height reduced to 39 mm; everything else as r60l6h26ri_sr5.
    "b39h26ri_sr5": {
        "xml": "assets/robot_selfrising_b39_h26_ri.xml",
        "q_half": 1.55,
        "q_min": -1.07,
        "q_max": 2.07,
        "q2_max": 0.8,
        "q_ctrl_max": 2.07,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "base 39 mm, 8.5x8.5, 26 cm arm, re-indexed horn",
    },
    # Same build trained from uniform random orientations (covers every face).
    "b39rq_sr5": {
        "xml": "assets/robot_selfrising_b39_h26_ri.xml",
        "q_half": 1.55,
        "q_min": -1.07,
        "q_max": 2.07,
        "q2_max": 0.8,
        "q_ctrl_max": 2.07,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "init_mode": "random_quat",
        "episode_steps": 600,
        "description": "b39 build, random-orientation training",
    },
    # Start from the stable "body up, propped on the extended arm" pose
    # (up_z ~ 0.93, q ~ (1.48, 0.14)). The policy's job is to retract both
    # joints to the vertical stand without dropping the body or clipping.
    "b39rq_ap_sr5": {
        "xml": "assets/robot_selfrising_b39_h26_ri.xml",
        "q_half": 1.55,
        "q_min": -1.07,
        "q_max": 2.07,
        "q2_max": 0.8,
        "q_ctrl_max": 2.07,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "init_mode": "armprop",
        "episode_steps": 600,
        "description": "b39 build, arm-prop stand-up training",
    },
    # Same 39 mm build without the horn re-index (plain +-1.55 rad shoulder).
    "b39h26_sr5": {
        "xml": "assets/robot_selfrising_b39_h26_plain.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "base 39 mm, 8.5x8.5, 26 cm arm, plain 180 deg shoulder",
    },
    # Same bulky build with the wide catch base (16x18 cm footprint). The
    # narrow 6x7.3 cm riser cannot catch the body once the arm has lifted it
    # off the ground, so that geometry settles propped on the extended arm.
    "r60l6w_sr5": {
        "xml": "assets/robot_selfrising_r60l6_wide.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "episode_steps": 600,
        "description": "base +6 cm wide 16x18, arm +6 cm, SR interface",
    },
    # split15, mixed init (60% canonical poses, 40% random orientations):
    # keeps the four-direction skill while adding upside-down recovery.
    "split15_mix_sr5": {
        "xml": "assets/robot_selfrising_split_r15_t15.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "init_mode": "mix",
        "description": "split15, mixed orientation training, SR interface",
    },
    # split15 geometry trained with uniform random initial orientations
    # (covers manual pushes that flip the robot upside down).
    "split15_rq_sr5": {
        "xml": "assets/robot_selfrising_split_r15_t15.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "init_mode": "random_quat",
        "description": "split15, random-orientation training, SR interface",
    },
    # Feasible tall build: base +15 mm and shoulder/tower +15 mm (total +30 mm).
    "split15_sr5": {
        "xml": "assets/robot_selfrising_split_r15_t15.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "description": "base +15 mm, tower +15 mm, SR interface",
    },
    # +6 cm shoulder height with a 6 cm longer arm (printed arm2 extension).
    "arm60long_sr5": {
        "xml": "assets/robot_selfrising_arm60_long.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar", "arm2_ext"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "description": "+6 cm shoulder, +6 cm long arm, SR interface",
    },
    # Tall-chassis variant: the whole robot raised 6 cm on a pedestal.
    "selfrising_tall_sr5": {
        "xml": "assets/robot_selfrising_tall.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "description": "tall chassis (+6 cm), SR-style interface",
    },
    # Same hardware, SelfRisingRobot-style slow interface (proven on PWM servos):
    # obs = up(3) + commanded targets(2); action = target increment * 0.08 rad.
    # No gyro/qdot feedback, so the policy is a smooth trajectory generator.
    "selfrising_sr5": {
        "xml": "assets/robot_selfrising.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "foot",
        "contact_geoms": ["foot_plate", "arm2_bar"],
        "obs_mode": "sr5",
        "action_mode": "increment",
        "description": "SelfRisingRobot print, SR-style slow interface",
    },
    # Juxi B-line reference geometry, kept for comparison only.
    "ptk7452": {
        "xml": "assets/robot_ptk7452.xml",
        "q_half": 1.55,
        "joint_source": "command",
        "body": "torso",
        "contact_geoms": ["pad"],
        "description": "Juxi B-line arm + 2x PTK7452MG (3.4 kg*cm @6V)",
    },
}


def _random_quat(rng: np.random.Generator) -> np.ndarray:
    """Uniform random unit quaternion in MuJoCo order (w, x, y, z)."""
    u1, u2, u3 = rng.random(3)
    return np.array([
        np.sqrt(u1) * np.cos(2.0 * np.pi * u3),
        np.sqrt(1.0 - u1) * np.sin(2.0 * np.pi * u2),
        np.sqrt(1.0 - u1) * np.cos(2.0 * np.pi * u2),
        np.sqrt(u1) * np.sin(2.0 * np.pi * u3),
    ])


def _roll_pitch_quat(roll: float, pitch: float) -> np.ndarray:
    cr = np.cos(roll / 2.0)
    sr = np.sin(roll / 2.0)
    cp = np.cos(pitch / 2.0)
    sp = np.sin(pitch / 2.0)
    return np.array([cr * cp, sr * cp, cr * sp, -sr * sp])


def _yaw_quat(yaw: float) -> np.ndarray:
    return np.array([np.cos(yaw / 2.0), 0.0, 0.0, np.sin(yaw / 2.0)])


def _quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


class SelfRightEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(
        self,
        robot: str = "selfrising",
        domain_randomization: bool = True,
        random_init: bool = True,
        episode_steps: int | None = None,
        render_mode: str | None = None,
        seed: int | None = None,
        poses: list[str] | None = None,
    ):
        super().__init__()
        if robot not in ROBOT_SPECS:
            raise ValueError(f"unknown robot {robot!r}; choose from {sorted(ROBOT_SPECS)}")
        spec = ROBOT_SPECS[robot]
        self.spec = spec
        self.robot = robot
        self.q_half = float(spec["q_half"])
        self.joint_source = str(spec["joint_source"])
        self.obs_mode = str(spec.get("obs_mode", "full"))
        self.action_mode = str(spec.get("action_mode", "absolute"))
        self.init_mode = str(spec.get("init_mode", "poses"))
        self.obs_dim = 5 if self.obs_mode == "sr5" else OBS_DIM
        self.render_mode = render_mode
        self.dr = domain_randomization
        self.random_init = random_init
        self.episode_steps = (
            int(spec.get("episode_steps", EPISODE_STEPS))
            if episode_steps is None
            else int(episode_steps)
        )
        # Highest joint target a scripted controller may command. The policy
        # itself stays within +-q_half; a wide-range shoulder servo can go
        # further (see PushStand in stand_homer.py).
        self.q_ctrl_max = float(spec.get("q_ctrl_max", self.q_half))
        # Asymmetric shoulder limits (re-indexed horn on a 180 deg servo):
        # q_min/q_max apply to joint 0; the elbow keeps +-q_half. An optional
        # q2_max narrows the elbow command range: at low base heights the
        # policy otherwise learns to sit on the bent forearm (elbow at its
        # limit) instead of standing up.
        q2_max = spec.get("q2_max")
        self.lim_lo = np.array([float(spec.get("q_min", -self.q_half)),
                                -float(q2_max) if q2_max else -self.q_half])
        self.lim_hi = np.array([float(spec.get("q_max", self.q_half)),
                                float(q2_max) if q2_max else self.q_half])
        # Scripted-controller overrides may use the elbow's full mechanical
        # range (the rescue pump needs it), while the policy stays narrower.
        self.ovr_lo = np.array([self.lim_lo[0], -self.q_half])
        self.ovr_hi = np.array([self.lim_hi[0], self.q_half])
        self.ctrl_override: np.ndarray | None = None
        self.poses = list(poses) if poses else list(POSE_RP)
        unknown = [p for p in self.poses if p not in POSE_RP]
        if unknown:
            raise ValueError(f"unknown poses {unknown}; choose from {sorted(POSE_RP)}")

        self.model = mujoco.MjModel.from_xml_path(
            str(Path(__file__).resolve().parent / str(spec["xml"]))
        )
        self.data = mujoco.MjData(self.model)
        self.phys_dt = float(self.model.opt.timestep)
        self.n_substeps = max(1, int(round(CTRL_DT / self.phys_dt)))
        self.n_settle_steps = max(1, int(round(SETTLE_TIME / self.phys_dt)))
        self._seed = seed

        self._ids()
        self._nominal = {
            "body_mass": self.model.body_mass.copy(),
            "body_inertia": self.model.body_inertia.copy(),
            "geom_friction": self.model.geom_friction.copy(),
            "actuator_gainprm": self.model.actuator_gainprm.copy(),
            "actuator_biasprm": self.model.actuator_biasprm.copy(),
            "actuator_forcerange": self.model.actuator_forcerange.copy(),
        }
        self.standing_height = self._compute_standing_height()
        self._prev_up = 1.0
        self._pose_name: str | None = None

        self.action_space = spaces.Box(-1.0, 1.0, (ACT_DIM,), np.float32)
        self.observation_space = spaces.Box(-np.inf, np.inf, (self.obs_dim,), np.float32)

        self._viewer = None
        self._buf = np.zeros((MAX_DELAY_STEPS + 1, ACT_DIM))
        self._att_buf = np.zeros((OBS_DELAY_STEPS + 1, 6))
        self._obs_delay = 0
        self._prev_cmd = np.zeros(ACT_DIM)
        self._last_qdot_cmd = np.zeros(ACT_DIM)
        self._prev_action = np.zeros(ACT_DIM)
        self._up_filt = np.array([0.0, 0.0, 1.0])
        self._step_count = 0

    def _ids(self) -> None:
        m = self.model
        self.torso_bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, self.spec["body"])
        self.root_jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "root")
        self.arm_jids = [
            mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "servo1_joint"),
            mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "servo2_joint"),
        ]
        self.arm_qpos_adr = [int(m.jnt_qposadr[j]) for j in self.arm_jids]
        self.arm_dof_adr = [int(m.jnt_dofadr[j]) for j in self.arm_jids]
        self.foot_gids = [
            mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, name)
            for name in self.spec["contact_geoms"]
        ]
        self.floor_gid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "floor")
        self.arm_bids = [
            mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "arm1"),
            mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "arm2"),
        ]

    def arm_penetration(self) -> float:
        """Deepest arm-vs-floor/base contact penetration, m (negative = overlap).

        Used by the scripted stand routine to abort instead of forcing the arm
        through the floor or the base. Visual meshes and collision proxies are
        both MuJoCo geoms, so this sees the deepest proxy contact.
        """
        m, d = self.model, self.data
        arm = [b for b in self.arm_bids if b >= 0]
        if not arm:
            return 0.0
        worst = 0.0
        for i in range(d.ncon):
            c = d.contact[i]
            b1 = int(m.geom_bodyid[c.geom1])
            b2 = int(m.geom_bodyid[c.geom2])
            if ((b1 in arm and b2 in (self.torso_bid, 0))
                    or (b2 in arm and b1 in (self.torso_bid, 0))):
                if float(c.dist) < worst:
                    worst = float(c.dist)
        return worst

    def _compute_standing_height(self) -> float:
        """Settle the nominal upright pose once to calibrate the height check."""
        d = mujoco.MjData(self.model)
        d.qpos[:] = 0.0
        d.qpos[0:3] = (0.0, 0.0, 0.08)
        d.qpos[3] = 1.0
        d.ctrl[:] = 0.0
        mujoco.mj_forward(self.model, d)
        for _ in range(self.n_settle_steps):
            d.ctrl[:] = 0.0
            mujoco.mj_step(self.model, d)
        return float(d.xpos[self.torso_bid, 2])

    # ------------------------------------------------------------------ model
    def _restore_model(self) -> None:
        for key, value in self._nominal.items():
            getattr(self.model, key)[:] = value

    def _randomize_model(self, rng: np.random.Generator) -> None:
        m = self.model
        # Payload variation (battery, screws, prints).
        f = rng.uniform(0.85, 1.15)
        m.body_mass[self.torso_bid] *= f
        m.body_inertia[self.torso_bid] *= f

        # Floor and foot friction; the dominant sim2real parameter here.
        m.geom_friction[self.floor_gid, 0] *= rng.uniform(0.8, 1.4)
        for gid in self.foot_gids:
            m.geom_friction[gid, 0] *= rng.uniform(0.8, 1.5)

        # Servo strength: stiffness and torque saturation, independently.
        for act in range(m.nu):
            kp_scale = rng.uniform(0.7, 1.3)
            m.actuator_gainprm[act, 0] *= kp_scale
            m.actuator_biasprm[act, 1] *= kp_scale
            tq = rng.uniform(0.75, 1.15) * abs(self._nominal["actuator_forcerange"][act, 1])
            m.actuator_forcerange[act] = (-tq, tq)

        mujoco.mj_setConst(m, self.data)

    # ------------------------------------------------------------------ reset
    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        rng = self.np_random
        mujoco.mj_resetData(self.model, self.data)
        self._restore_model()
        if self.dr:
            self._randomize_model(rng)

        pose_name = None
        if options is not None and options.get("pose") is not None:
            pose_name = str(options["pose"])
            roll, pitch = POSE_RP[pose_name]
            quat = _roll_pitch_quat(roll, pitch)
            quat = _quat_mul(_yaw_quat(float(options.get("yaw", 0.0))), quat)
            q0 = np.asarray(options.get("arm_q", [0.0, 0.0]), dtype=np.float64)
            z0 = float(options.get("z0", 0.08))
        elif options is not None and options.get("quat") is not None:
            quat = np.asarray(options["quat"], dtype=np.float64)
            q0 = np.asarray(options.get("arm_q", [0.0, 0.0]), dtype=np.float64)
            z0 = float(options.get("z0", 0.08))
        elif self.init_mode == "armprop" and self.random_init:
            # Stable arm-prop pose: body leaning on the extended arm.
            roll = rng.uniform(0.30, 0.48)
            quat = _roll_pitch_quat(roll, 0.0)
            quat = _quat_mul(_yaw_quat(rng.uniform(-np.pi, np.pi)), quat)
            q0 = np.array([rng.uniform(1.40, 1.56), rng.uniform(0.05, 0.25)])
            z0 = 0.10
        elif self.init_mode in ("random_quat", "mix") and self.random_init:
            if self.init_mode == "mix" and rng.random() < 0.6:
                pose_name = str(rng.choice(self.poses))
                roll, pitch = POSE_RP[pose_name]
                roll += rng.uniform(-0.10, 0.10)
                pitch += rng.uniform(-0.10, 0.10)
                quat = _roll_pitch_quat(roll, pitch)
                quat = _quat_mul(_yaw_quat(rng.uniform(-np.pi, np.pi)), quat)
            else:
                quat = _random_quat(rng)
            z0 = 0.08
            q0 = np.zeros(ACT_DIM)
        elif self.random_init:
            pose_name = str(rng.choice(self.poses))
            roll, pitch = POSE_RP[pose_name]
            roll += rng.uniform(-0.10, 0.10)
            pitch += rng.uniform(-0.10, 0.10)
            quat = _roll_pitch_quat(roll, pitch)
            quat = _quat_mul(_yaw_quat(rng.uniform(-np.pi, np.pi)), quat)
            z0 = 0.08
            q0 = np.zeros(ACT_DIM)
        else:
            quat = np.array([1.0, 0.0, 0.0, 0.0])
            z0 = 0.08
            q0 = np.zeros(ACT_DIM)
        self._pose_name = pose_name

        self.data.qpos[0:3] = (0.0, 0.0, z0)
        self.data.qpos[3:7] = quat
        for i, adr in enumerate(self.arm_qpos_adr):
            self.data.qpos[adr] = q0[i]
        self.data.qvel[:] = 0.0
        self.data.ctrl[:] = np.clip(q0, self.lim_lo, self.lim_hi)
        mujoco.mj_forward(self.model, self.data)

        # Let it fall and come to rest so the policy starts from a real fallen
        # pose, not mid-air (deployment also starts from the ground).
        for _ in range(self.n_settle_steps):
            mujoco.mj_step(self.model, self.data)

        self._prev_cmd = np.clip(q0, self.lim_lo, self.lim_hi)
        self.ctrl_override = None
        self._last_qdot_cmd = np.zeros(ACT_DIM)
        self._prev_action = self._prev_cmd / self.q_half
        self._buf[:] = self._prev_cmd
        self._step_count = 0

        up = self._up_body()
        self._up_filt = up.copy()
        self._prev_up = float(up[2])
        self._obs_delay = int(rng.integers(0, OBS_DELAY_STEPS + 1)) if self.dr else 0
        self._att_buf[:, :3] = up
        self._att_buf[:, 3:] = 0.0
        self._up_tau = rng.uniform(0.02, 0.15) if self.dr else 0.05
        self._acc_noise = rng.uniform(0.02, 0.06) if self.dr else 0.0
        self._gyro_noise = rng.uniform(0.02, 0.06) if self.dr else 0.0
        self._gyro_bias = rng.uniform(-0.05, 0.05, 3) if self.dr else np.zeros(3)
        self._delay = int(rng.integers(0, MAX_DELAY_STEPS + 1)) if self.dr else 1
        # Real hobby servos ignore small position errors (deadband) and have
        # gear backlash; model a deadband of up to ~1.7 deg.
        self._deadband = rng.uniform(0.0, 0.03) if self.dr else 0.0
        self._servo_offset = rng.uniform(-0.04, 0.04, ACT_DIM) if self.dr else np.zeros(ACT_DIM)
        self._q_noise = rng.uniform(0.002, 0.008) if self.dr else 0.0
        self._qd_noise = rng.uniform(0.05, 0.3) if self.dr else 0.0

        obs = self._obs()
        return obs, {}

    # ------------------------------------------------------------- observation
    def _up_body(self) -> np.ndarray:
        # body->world rotation R; world up in body frame = R.T @ e_z = R[2, :]
        return self.data.xmat[self.torso_bid].reshape(3, 3)[2, :].copy()

    def _obs(self) -> np.ndarray:
        rng = self.np_random
        up = self._up_body()
        alpha = CTRL_DT / (self._up_tau + CTRL_DT)
        self._up_filt += alpha * (up - self._up_filt)
        n = self._up_filt / max(np.linalg.norm(self._up_filt), 1e-9)
        n = n + rng.normal(0.0, self._acc_noise, 3)
        n /= max(np.linalg.norm(n), 1e-9)

        omega = self.data.qvel[3:6] + self._gyro_bias
        omega = omega + rng.normal(0.0, self._gyro_noise, 3)

        q = np.array([self.data.qpos[a] for a in self.arm_qpos_adr])
        if self.joint_source == "actual":
            qd = np.array([self.data.qvel[a] for a in self.arm_dof_adr])
        else:
            q = self._prev_cmd.copy()
            qd = self._last_qdot_cmd.copy()
        q = q + rng.normal(0.0, self._q_noise, ACT_DIM)
        qd = qd + rng.normal(0.0, self._qd_noise, ACT_DIM)

        # Real IMU + Mahony output lags; the policy sees a delayed attitude.
        self._att_buf[1:] = self._att_buf[:-1]
        self._att_buf[0, :3] = n
        self._att_buf[0, 3:] = omega
        att = self._att_buf[self._obs_delay]

        if self.obs_mode == "sr5":
            obs = np.concatenate([att[:3], q]).astype(np.float32)
        else:
            obs = np.concatenate([att[:3], att[3:], q, qd]).astype(np.float32)
        return obs

    # ------------------------------------------------------------------- step
    def step(self, action: np.ndarray):
        rng = self.np_random
        action = np.clip(np.asarray(action, dtype=np.float64), -1.0, 1.0)

        if self.ctrl_override is not None:
            # A scripted controller (PushStand) sets the target directly; the
            # servo latency/deadband path below still applies.
            cmd = np.clip(np.asarray(self.ctrl_override, dtype=np.float64),
                          self.ovr_lo, self.ovr_hi)
            self.ctrl_override = None
        elif self.action_mode == "increment":
            cmd = np.clip(self._prev_cmd + action * ACTION_DELTA,
                          self.lim_lo, self.lim_hi)
        else:
            target = action * self.q_half
            cmd = np.clip(target, self._prev_cmd - MAX_CMD_RATE, self._prev_cmd + MAX_CMD_RATE)
        self._last_qdot_cmd = (cmd - self._prev_cmd) / CTRL_DT
        self._prev_cmd = cmd

        # Actuator latency: the servo receives the command `delay` steps later.
        self._buf[1:] = self._buf[:-1]
        self._buf[0] = cmd
        target = self._buf[self._delay] + self._servo_offset
        if self._deadband > 0.0:
            q_act = np.array([self.data.qpos[a] for a in self.arm_qpos_adr])
            for i in range(ACT_DIM):
                if abs(target[i] - q_act[i]) < self._deadband:
                    target[i] = q_act[i]
        self.data.ctrl[:] = target

        for _ in range(self.n_substeps):
            mujoco.mj_step(self.model, self.data)
        self._step_count += 1

        up = self._up_body()
        h = float(self.data.xpos[self.torso_bid, 2])
        height_ok = abs(h - self.standing_height) < HEIGHT_TOL
        settled = bool(np.max(np.abs(self._prev_cmd)) < Q_STAND_TOL)
        # Success requires the arm-vertical stand pose, not just the body up:
        # the tall-riser geometry can also rest propped on the extended arm,
        # which is not the pose the robot has to finish in.
        upright = bool(up[2] > UP_STAND and height_ok and settled)
        progress = float(up[2]) - self._prev_up
        self._prev_up = float(up[2])

        omega = self.data.qvel[3:6]
        dact = action - self._prev_action
        self._prev_action = action.copy()
        tau = self.data.actuator_force
        pen = self.arm_penetration()
        if self.joint_source == "actual":
            q_now = np.array([self.data.qpos[a] for a in self.arm_qpos_adr])
        else:
            q_now = self._prev_cmd

        reward = (
            2.0 * max(float(up[2]), 0.0)
            # With the body up, the arm earns more reward the closer it is to
            # the vertical pose: without this the policy parks in a stable
            # "standing on the extended arm" pose and never lifts out.
            + 2.0 * max(float(up[2]), 0.0) * float(np.mean(np.cos(q_now)))
            + 4.0 * progress
            + 3.0 * float(upright)
            + 4.0 * float(upright) * float(np.exp(-float(np.mean(q_now ** 2)) / 0.05))
            - 1.0 * float(upright) * float(np.sum(np.abs(q_now)))
            - 0.005 * float(np.sum(omega ** 2))
            - 0.05 * float(np.sum(dact ** 2))
            - 0.0005 * float(np.sum(tau ** 2))
            - 0.4 * float(upright) * float(np.mean(q_now ** 2))
            - 100.0 * max(0.0, -pen - 0.001)
        )

        obs = self._obs()
        truncated = self._step_count >= self.episode_steps
        info = {
            "up_z": float(up[2]),
            "height": h,
            "height_ok": height_ok,
            "settled": settled,
            "upright": upright,
            "pose": self._pose_name,
            "actuator_force": tau.copy(),
            "pen": pen,
        }
        return obs, float(reward), False, truncated, info

    # ----------------------------------------------------------------- render
    def render(self):
        if self.render_mode != "human":
            return
        if self._viewer is None:
            import mujoco.viewer
            self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
        self._viewer.sync()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None


def make_env(rank: int, seed: int = 0, robot: str = "selfrising", homer: bool = False, **kwargs):
    """VecEnv factory. Must be a top-level function to be picklable."""
    def _init():
        env = SelfRightEnv(robot=robot, seed=seed + rank, **kwargs)
        if homer:
            from .stand_homer import HomerWrapper

            env = HomerWrapper(env)
        return env
    return _init
