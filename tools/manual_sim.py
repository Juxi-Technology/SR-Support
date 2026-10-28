"""Keyboard-driven MuJoCo bench for the b39 build, with full logging.

The operator drives the two joints from the keyboard; every key event and
every 20 ms control tick's attitude is written to logs/manual_sim_log.csv so
the demonstrated manoeuvre can be analysed afterwards.

Keys:
  LEFT / RIGHT   shoulder target  -0.10 / +0.10 rad  (clamped to [-1.07, 2.07])
  DOWN / UP      elbow target     -0.10 / +0.10 rad  (clamped to [-1.55, 1.55])
  R              reset the robot to a random fallen pose
  U              reset upright
  C              re-centre both targets (0, 0)
  Space          pause / resume

Mouse: double-click a body to select it, then Ctrl+right-drag to push.

Run:  .venv/Scripts/python.exe tools/manual_sim.py
"""

from __future__ import annotations

import math
import time
from datetime import datetime
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "training/b_line/assets/robot_selfrising_b39_h26_ri.xml"
LOG = ROOT / "logs" / "manual_sim_log.csv"

SH_MIN, SH_MAX = -1.07, 2.07
EL_MAX = 1.55
STEP = 0.10
CTRL_DT = 0.02
PHYS_DT = 0.001   # default; the model's timestep is used when stepping
SUB = int(round(CTRL_DT / PHYS_DT))

target = np.zeros(2)
paused = False


def quat_aa(ax, a):
    ax = np.asarray(ax, float)
    ax /= np.linalg.norm(ax)
    s = math.sin(a / 2)
    return np.array([math.cos(a / 2), ax[0] * s, ax[1] * s, ax[2] * s])


def reset_robot(m, d, upright=False):
    mujoco.mj_resetData(m, d)
    d.qpos[0:3] = (0.0, 0.0, 0.12)
    if upright:
        d.qpos[3:7] = (1.0, 0.0, 0.0, 0.0)
    else:
        ax = np.random.randn(3)
        d.qpos[3:7] = quat_aa(ax, np.random.uniform(0, 2 * math.pi))
    d.qpos[7:9] = (0.0, 0.0)
    d.ctrl[:] = 0.0
    target[:] = 0.0


def main() -> None:
    m = mujoco.MjModel.from_xml_path(str(XML))
    d = mujoco.MjData(m)
    foot = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "foot")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    f = LOG.open("a", encoding="utf-8")
    f.write(f"--- session {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
    f.write("time,event,q1_tgt,q2_tgt,q1_act,q2_act,up_x,up_y,up_z\n")

    def log_event(event: str):
        up = d.xmat[foot].reshape(3, 3)[2]
        f.write(f"{datetime.now():%H:%M:%S.%f}"[:-3] + f",{event},"
                f"{target[0]:+.3f},{target[1]:+.3f},"
                f"{d.qpos[7]:+.3f},{d.qpos[8]:+.3f},"
                f"{up[0]:+.3f},{up[1]:+.3f},{up[2]:+.3f}\n")
        f.flush()

    def key_cb(keycode):
        global paused
        assert _viewer is not None
        k = keycode
        if k == 263:      # LEFT
            target[0] = max(SH_MIN, target[0] - STEP); log_event("key:sh-")
        elif k == 262:    # RIGHT
            target[0] = min(SH_MAX, target[0] + STEP); log_event("key:sh+")
        elif k == 264:    # DOWN
            target[1] = max(-EL_MAX, target[1] - STEP); log_event("key:el-")
        elif k == 265:    # UP
            target[1] = min(EL_MAX, target[1] + STEP); log_event("key:el+")
        elif k == 82:     # R
            reset_robot(m, d, upright=False); log_event("reset:random")
        elif k == 85:     # U
            reset_robot(m, d, upright=True); log_event("reset:upright")
        elif k == 67:     # C
            target[:] = 0.0; log_event("centre")
        elif k == 32:     # SPACE
            paused = not paused; log_event("pause" if paused else "resume")

    global _viewer
    with mujoco.viewer.launch_passive(m, d, key_callback=key_cb) as viewer:
        _viewer = viewer
        reset_robot(m, d, upright=False)
        log_event("session-start")
        last = time.time()
        n = 0
        try:
            while viewer.is_running():
                now = time.time()
                if now - last < CTRL_DT:
                    time.sleep(0.002)
                    continue
                last = now
                if not paused:
                    d.ctrl[:] = target
                    for _ in range(int(round(CTRL_DT / m.opt.timestep))):
                        d.xfrc_applied[:] = 0.0
                        mujoco.mjv_applyPerturbForce(m, d, viewer.perturb)
                        mujoco.mj_step(m, d)
                    n += 1
                    if n % 5 == 0:  # 10 Hz pose log
                        up = d.xmat[foot].reshape(3, 3)[2]
                        f.write(f"{datetime.now():%H:%M:%S.%f}"[:-3] + ",tick,"
                                f"{target[0]:+.3f},{target[1]:+.3f},"
                                f"{d.qpos[7]:+.3f},{d.qpos[8]:+.3f},"
                                f"{up[0]:+.3f},{up[1]:+.3f},{up[2]:+.3f}\n")
                        f.flush()
                viewer.sync()
        finally:
            f.write("--- session end ---\n")
            f.close()


_viewer = None

if __name__ == "__main__":
    main()
