"""Kinematic probe of the stalled roll_neg press attitude.

Question: with the body frozen at the recorded 5 V stall attitude
(quat 0.891 0.044 -0.446 0.072 from the flash snapshot of the failed
-X attempt, q=(-1.07, 0.8)) and the foot snapped to the floor, does
extending the elbow (q2 0.8 -> 0) push the arm INTO the floor (floor
reaction lifts the body = useful kick) or LIFT the tip off the floor
(body would sag = useless / harmful)?

Sign convention: arm min-z decreasing with q2 extension => the tip would
penetrate the floor => in reality the floor pushes the shoulder up.

Also prints the horizontal lever of the arm contact vs the foot contact and
the model masses, to compare the static torque demand against the ~2.8
kg*cm a PTK7452MG gives at 5 V.
"""
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(r"D:\Project\SR-Support")
m = mujoco.MjModel.from_xml_path(str(ROOT / "hardware/v1/robot_v1.xml"))
d = mujoco.MjData(m)


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
    return q / n


def geom_table(body_names):
    ids = {int(m.body(nm).id) for nm in body_names}
    table = []
    for g in range(m.ngeom):
        if int(m.geom_bodyid[g]) not in ids:
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


foot = geom_table(["foot"])
arm = geom_table(["arm1", "arm2"])


def lowest(table):
    best = (np.inf, None, None)
    for t, g, verts, size in table:
        R = d.geom_xmat[g].reshape(3, 3)
        x = d.geom_xpos[g]
        if t == mujoco.mjtGeom.mjGEOM_MESH:
            w = verts @ R.T + x
            i = int(np.argmin(w[:, 2]))
            if w[i, 2] < best[0]:
                best = (float(w[i, 2]), w[i, :2].copy(), g)
        else:
            z = float(x[2] - np.abs(R[2, :]).dot(size))
            if z < best[0]:
                best = (z, x[:2].copy(), g)
    return best


def min_z(table):
    return lowest(table)[0]


# joint addresses
qa = [int(m.jnt_qposadr[m.joint(f"servo{i + 1}_joint").id]) for i in range(2)]

# total mass breakdown
print("masses:")
tot = 0.0
for b in range(m.nbody):
    nm = m.body(b).name
    mm = float(m.body_subtreemass[b])
    if b != 0 and nm:
        pass
print(f"  total model mass = {float(m.body_subtreemass[0]):.4f} kg")
for nm in ("foot", "arm1", "arm2"):
    b = m.body(nm).id
    print(f"  {nm:5s} subtree = {float(m.body_subtreemass[b]) * 1000.0:6.1f} g")

# recorded stall attitude (raw IMU quat + IMU_YAW90 mapping used by live_twin)
raw = np.array([0.891, 0.044, -0.446, 0.072])
q_z90 = np.array([np.cos(np.pi / 4), 0.0, 0.0, np.sin(np.pi / 4)])
qb = q_normalize(qmul(raw, q_z90))

d.qpos[:] = 0.0
d.qpos[0:3] = (0.0, 0.0, 0.2)
d.qpos[3:7] = qb


def snap_and_set(q1, q2):
    d.qpos[qa[0]] = q1
    d.qpos[qa[1]] = q2
    mujoco.mj_forward(m, d)
    dz = min_z(foot)
    d.qpos[2] -= dz
    mujoco.mj_forward(m, d)


def up_vec():
    R = d.xmat[m.body("foot").id].reshape(3, 3)
    return R.T @ np.array([0.0, 0.0, 1.0])


print("\nattitude check (body up should be ~(0.015,-0.801,0.599)):")
snap_and_set(-1.07, 0.8)
print("  up =", np.round(up_vec(), 3))

print("\nq2 sweep at q1=-1.07 (body attitude frozen):")
print("   q2    arm_min_z   foot_min_z   arm_xy            foot_xy           horiz_dist")
for q2 in [1.5, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2, 0.0, -0.3]:
    snap_and_set(-1.07, q2)
    az, axy, ag = lowest(arm)
    fz, fxy, fg = lowest(foot)
    hd = float(np.linalg.norm(axy - fxy)) if axy is not None else float("nan")
    print(f"  {q2:5.2f}   {az:9.4f}   {fz:9.4f}   "
          f"({axy[0]:+.3f},{axy[1]:+.3f})  ({fxy[0]:+.3f},{fxy[1]:+.3f})  {hd:.4f}")

print("\nq1 sweep at q2=0.8 (arm contact vs shoulder stop):")
for q1 in [-1.07, -0.95, -0.8, -0.6]:
    snap_and_set(q1, 0.8)
    az, axy, ag = lowest(arm)
    fz, fxy, fg = lowest(foot)
    print(f"  q1={q1:5.2f}  q2=0.8  arm_min_z={az:+.4f}  arm_xy=({axy[0]:+.3f},{axy[1]:+.3f})")

# static torque demand about the foot's floor contact line at the stall,
# from the model COM (informative only: model masses are printed-part only)
snap_and_set(-1.07, 0.8)
cop = lowest(foot)[1]
com = d.subtree_com[m.body("foot").id]
# force to the lowest foot vertex; horizontal vector from it to the COM
r = com[:2] - cop
m_tot = float(m.body_subtreemass[0])
# torque about the horizontal axis perpendicular to the tilt direction:
# tilt is along -y (up=(0,-0.8,0.6)) so the pivot axis is x
lever_y = float(r[1])
tau = m_tot * 9.81 * abs(lever_y)
print(f"\nstatic torque about the foot rim (axis x): lever_y={lever_y:+.4f} m, "
      f"m={m_tot * 1000:.0f} g -> tau={tau:.4f} N*m "
      f"(PTK7452MG at 5 V ~ {2.8 * 0.0980665:.3f} N*m, at 6 V ~ {3.4 * 0.0980665:.3f} N*m)")
