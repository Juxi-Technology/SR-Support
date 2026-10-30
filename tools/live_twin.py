"""Live MuJoCo twin of the real SR-Support robot.

Mirrors the real robot's attitude and commanded joint angles in a MuJoCo
viewer while the firmware runs.

Data source (serial 115200):
  * 'T w x y z q1 q2' - 50 Hz twin stream (firmware key 'd'). Sent by this
    tool automatically unless T lines are already arriving.
  * fallbacks: 'F ...' fast-log bursts ('l' on the robot, 50 Hz for 3 s)
    and the 4 Hz status line ('up ... | q ... | state'). Those carry no
    quaternion; the yaw is then reconstructed by the shortest-arc rotation
    from the up vector, so the twin may face an arbitrary heading.

Frames: the firmware up_body() ("R^T e_z, third row of R") is exactly the
MuJoCo body xmat row 2, so the sim poses match the robot. The raw attitude
quat needs the config.h IMU_YAW90 correction (disable with --no-yaw90 when
that build flag is off). The robot's ground position is unknown to the
firmware; the twin keeps it at the origin and slides it down so the base
rests on the floor (a pressing arm pose may dip below the floor plane: the
servo stalls against the real floor, the commanded angle does not).

Usage:
  .venv/Scripts/python.exe tools/live_twin.py --port COM27
  .venv/Scripts/python.exe tools/live_twin.py --replay logs/hw_fast_20261022_180610.txt
  .venv/Scripts/python.exe tools/live_twin.py --port COM27 --xml training/b_line/assets/robot_v1_270.xml

Note: opening the port can reset the ESP32 (DTR), as with the other hw
tools. The twin is read-only apart from the single 'd' toggle it may send.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
XML_V1 = ROOT / "training/b_line/assets/robot_v1.xml"

F_RE = re.compile(
    r"^F\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s*\|\s*"
    r"([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s*\|\s*"
    r"([-+0-9.]+)\s+([-+0-9.]+)\s*\|")
T_RE = re.compile(
    r"^T\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)"
    r"\s+([-+0-9.]+)\s+([-+0-9.]+)")
UP_RE = re.compile(
    r"^up\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+).*?\|\s*q\s+"
    r"([-+0-9.]+)\s+([-+0-9.]+)\s*\|")

Q_Z90 = np.array([np.cos(np.pi / 4), 0.0, 0.0, np.sin(np.pi / 4)])
Q_ZM90 = np.array([np.cos(np.pi / 4), 0.0, 0.0, -np.sin(np.pi / 4)])


def qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ])


def q_normalize(q):
    n = float(np.linalg.norm(q))
    return q / n if n > 1e-9 else np.array([1.0, 0.0, 0.0, 0.0])


def q_from_up(u):
    """Shortest-arc quat R with R u = e_z (yaw-free, matches the sim up)."""
    u = np.asarray(u, dtype=np.float64)
    u = u / max(float(np.linalg.norm(u)), 1e-9)
    w = 1.0 + u[2]
    if w < 1e-6:  # pointing straight down: 180 deg about body x
        return np.array([0.0, 1.0, 0.0, 0.0])
    return q_normalize(np.array([w, u[1], -u[0], 0.0]))


class Telemetry:
    """Latest robot state parsed from one telemetry line."""

    def __init__(self):
        self.quat = None      # raw IMU-frame attitude quat (w,x,y,z) or None
        self.up = None        # body-frame up vector or None
        self.q = np.zeros(2)  # commanded joints
        self.kind = "-"
        self.stamp = 0.0

    def feed(self, line: str, now: float) -> bool:
        quat_live = self.kind == "T" and now - self.stamp < 1.0
        m = T_RE.match(line) if line.startswith("T ") else None
        if m:
            v = [float(x) for x in m.groups()]
            self.quat = q_normalize(np.array(v[:4]))
            self.q = np.array(v[4:6])
            self.up = None
            self.kind = "T"
            self.stamp = now
            return True
        m = F_RE.match(line) if line.startswith("F ") else None
        if m:
            if quat_live:
                return False   # the up-only view would kick the yaw
            v = [float(x) for x in m.groups()]
            self.up = np.array(v[0:3])
            self.q = np.array(v[6:8])
            self.quat = None
            self.kind = "F"
            self.stamp = now
            return True
        m = UP_RE.match(line) if line.startswith("up ") else None
        if m:
            if quat_live:
                return False   # keep the quat orientation; see above
            v = [float(x) for x in m.groups()]
            self.up = np.array(v[0:3])
            self.q = np.array(v[3:5])
            self.quat = None
            self.kind = "up"
            self.stamp = now
            return True
        return False


class Twin:
    def __init__(self, xml_path, yaw90=True):
        self.model = mujoco.MjModel.from_xml_path(str(xml_path))
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.qpos_adr = [int(m.jnt_qposadr[m.joint(f"servo{i + 1}_joint").id])
                         for i in range(2)]
        # geom tables for the floor snapping: the base ("foot") always sits
        # on the ground on the real robot; snapping by the whole robot would
        # lift the base whenever the commanded arm pose presses deeper than
        # the floor (the real servo stalls against the floor, the command
        # does not), which showed up as the chassis hovering.
        self.geoms = self._geom_table({int(m.body("foot").id)})
        # arm geoms for the floor contact clamp: the real arm cannot go
        # through the floor; the commanded angles can. The displayed pose
        # stops at the contact angle, like the stalled servo.
        self.arm_geoms = self._geom_table({
            int(m.body("arm1").id), int(m.body("arm2").id)})
        self.disp_q = np.zeros(2)
        self.yaw90 = yaw90

    def _geom_table(self, body_ids):
        m = self.model
        table = []
        for g in range(m.ngeom):
            if int(m.geom_bodyid[g]) not in body_ids:
                continue
            t = m.geom_type[g]
            if t == mujoco.mjtGeom.mjGEOM_MESH:
                mid = int(m.geom_dataid[g])
                a = int(m.mesh_vertadr[mid])
                n = int(m.mesh_vertnum[mid])
                table.append((t, g, m.mesh_vert[a:a + n].copy(), None))
            else:
                table.append((t, g, None, m.geom_size[g].copy()))
        return table

    def _table_min_z(self, table):
        d = self.data
        best = np.inf
        for t, g, verts, size in table:
            R = d.geom_xmat[g].reshape(3, 3)
            x = d.geom_xpos[g]
            if t == mujoco.mjtGeom.mjGEOM_MESH:
                best = min(best, float((verts @ R.T + x)[:, 2].min()))
            elif t == mujoco.mjtGeom.mjGEOM_BOX:
                best = min(best, float(x[2] - np.abs(R[2, :]).dot(size)))
            elif t == mujoco.mjtGeom.mjGEOM_CYLINDER:
                best = min(best, float(x[2] - np.hypot(R[2, 0], R[2, 1]) * size[0]
                                       - abs(R[2, 2]) * size[1]))
        return best

    def _set_arm(self, q):
        for i in range(2):
            self.data.qpos[self.qpos_adr[i]] = float(np.clip(q[i], -3.0, 3.0))
        mujoco.mj_forward(self.model, self.data)
        return self._table_min_z(self.arm_geoms)

    def _arm_floor_clamp(self, cmd):
        """Largest step prev->cmd whose arm stays at/above the floor."""
        tol = -0.002
        prev = self.disp_q
        if self._set_arm(cmd) >= tol:
            return cmd
        if self._set_arm(prev) < tol:
            # already penetrating (orientation jumped under the arm): keep
            # the command rather than freezing at a wrong pose
            self._set_arm(cmd)
            return cmd
        lo, hi = 0.0, 1.0
        for _ in range(11):
            mid = 0.5 * (lo + hi)
            if self._set_arm(prev + mid * (cmd - prev)) >= tol:
                lo = mid
            else:
                hi = mid
        q = prev + lo * (cmd - prev)
        self._set_arm(q)
        return q

    def apply(self, tel: Telemetry):
        if tel.quat is not None:
            q = qmul(tel.quat, Q_Z90) if self.yaw90 else tel.quat.copy()
        elif tel.up is not None:
            q = q_from_up(tel.up)
        else:
            return
        m, d = self.model, self.data
        d.qpos[:] = 0.0
        d.qpos[0:3] = (0.0, 0.0, 0.15)
        d.qpos[3:7] = q
        cmd = np.clip(tel.q, -3.0, 3.0)
        for i in range(2):
            d.qpos[self.qpos_adr[i]] = float(cmd[i])
        mujoco.mj_forward(m, d)
        dz = self._table_min_z(self.geoms)
        d.qpos[2] -= dz
        mujoco.mj_forward(m, d)
        self.disp_q = self._arm_floor_clamp(cmd)


def run_replay(twin, viewer, path, speed):
    tel = Telemetry()
    t0 = time.time()
    n = 0
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        if not viewer.is_running():
            return
        now = time.time()
        if tel.feed(line, now):
            n += 1
            twin.apply(tel)
            viewer.sync()
            if tel.kind == "up":
                time.sleep(0.25 / speed)
            else:
                time.sleep(0.02 / speed)
    # hold the last pose until the window closes
    while viewer.is_running():
        viewer.sync()
        time.sleep(0.03)
    print(f"replay done: {n} state lines")


def run_serial(twin, viewer, port, baud, enable):
    import serial
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 0.01
    ser.dtr = False
    ser.rts = False
    ser.open()
    print(f"connected {port} @ {baud}")
    tel = Telemetry()
    buf = ""
    n_upd = 0
    t_open = time.time()
    sent_toggle = False
    last_stats = time.time()
    last_sync = 0.0
    while viewer.is_running():
        now = time.time()
        if enable and not sent_toggle and now - t_open > 2.0:
            if tel.kind == "T" and now - tel.stamp < 0.5:
                print("twin stream already on", flush=True)
            else:
                ser.write(b"d")
                print("sent 'd' to enable the 50 Hz twin stream "
                      "(needs the twin-log firmware)", flush=True)
            sent_toggle = True
        try:
            chunk = ser.read(4096)
        except Exception as e:
            print("serial read failed:", e, flush=True)
            time.sleep(0.2)
            continue
        updated = False
        if chunk:
            buf += chunk.decode("utf-8", "replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if tel.feed(line.strip(), now):
                    updated = True
        if updated:
            n_upd += 1
            twin.apply(tel)
        # render on new data (50 Hz) plus a 20 Hz heartbeat for the UI/camera
        if updated or now - last_sync > 0.05:
            viewer.sync()
            last_sync = now
        if now - last_stats > 5.0:
            last_stats = now
            age = (now - tel.stamp) if tel.stamp else float("inf")
            print(f"updates={n_upd:6d} rate~{n_upd / (now - t_open):4.1f}/s "
                  f"src={tel.kind} age={age:4.1f}s", flush=True)
        time.sleep(0.002)
    ser.close()


def main():
    ap = argparse.ArgumentParser(description="MuJoCo live twin of the robot")
    ap.add_argument("--port", default=None, help="serial port, e.g. COM27")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--replay", default=None, help="replay a telemetry/log file")
    ap.add_argument("--replay-speed", type=float, default=1.0)
    ap.add_argument("--xml", default=str(XML_V1))
    ap.add_argument("--no-yaw90", action="store_true",
                    help="build has IMU_YAW90 disabled")
    ap.add_argument("--no-enable", action="store_true",
                    help="do not send the 'd' twin-stream toggle")
    args = ap.parse_args()
    if not args.port and not args.replay:
        ap.error("need --port or --replay")

    twin = Twin(args.xml, yaw90=not args.no_yaw90)
    with mujoco.viewer.launch_passive(twin.model, twin.data) as viewer:
        viewer.cam.lookat[:] = (0.0, 0.0, 0.06)
        viewer.cam.distance = 0.6
        viewer.cam.azimuth = 135
        viewer.cam.elevation = -18
        if args.replay:
            run_replay(twin, viewer, args.replay, args.replay_speed)
        else:
            run_serial(twin, viewer, args.port, args.baud,
                       enable=not args.no_enable)


if __name__ == "__main__":
    main()
