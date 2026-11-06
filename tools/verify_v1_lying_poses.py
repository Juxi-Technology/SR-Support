"""Check that the v1 lying poses settle physically and get-ups still work.

The servos are released during the settle (zero torque), so gravity decides
the resting arm pose: the arm falls until its far end rests on the floor -
the passive-robot rest pose. The servos then engage at the settled angles
and the reference+feedback executor runs the pose sequence (v1 sim refs).

Prints, per pose: settled joint angles, lowest point of each arm below the
shoulder, floor contacts, then the get-up result. With --out it also writes
a 2x2 montage of the settled poses.

Usage:
  python tools/verify_v1_lying_poses.py --out logs/v1_lying_limp.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from training.b_line.getup_env import B39GetupEnv  # noqa: E402
from training.b_line.getup_executor import GetupExecutor, pose_from_up  # noqa: E402
from training.b_line.getup_reference_v1 import SEQUENCES_V1  # noqa: E402

XML_V1 = ROOT / "hardware/v1/robot_v1.xml"
POSES = ("roll_pos", "roll_neg", "pitch_pos", "pitch_neg")


def geom_min_z(m, d, g):
    t = m.geom_type[g]
    R = d.geom_xmat[g].reshape(3, 3)
    x = d.geom_xpos[g]
    if t == mujoco.mjtGeom.mjGEOM_MESH:
        mid = int(m.geom_dataid[g])
        a = int(m.mesh_vertadr[mid])
        n = int(m.mesh_vertnum[mid])
        w = m.mesh_vert[a:a + n] @ R.T + x
        return float(w[:, 2].min())
    if t == mujoco.mjtGeom.mjGEOM_BOX:
        s = m.geom_size[g]
        return float(x[2] - np.abs(R[2, :]).dot(s))
    if t == mujoco.mjtGeom.mjGEOM_CYLINDER:
        s = m.geom_size[g]
        r, h = s[0], s[1]
        return float(x[2] - np.hypot(R[2, 0], R[2, 1]) * r - abs(R[2, 2]) * h)
    return float(x[2])


def body_min_z(m, d, bid):
    return min(geom_min_z(m, d, g) for g in range(m.ngeom)
               if int(m.geom_bodyid[g]) == bid)


def floor_contacts(m, d):
    out = []
    for i in range(d.ncon):
        c = d.contact[i]
        b1 = int(m.geom_bodyid[c.geom1])
        b2 = int(m.geom_bodyid[c.geom2])
        if (b1 == 0) != (b2 == 0):
            other = b2 if b1 == 0 else b1
            out.append((mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, other),
                        round(float(c.dist), 4)))
    return sorted(set(out), key=lambda t: t[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="write a 2x2 montage here")
    args = ap.parse_args()

    env = B39GetupEnv(fallen_poses=POSES, xml_path=XML_V1, limp_settle=True)
    m, d = env.model, env.data
    arm_bids = [m.body("arm1").id, m.body("arm2").id]

    renderer = None
    tiles = []
    if args.out:
        renderer = mujoco.Renderer(m, height=360, width=480)
        cam = mujoco.MjvCamera()
        cam.lookat[:] = (0.0, 0.0, 0.04)
        cam.distance = 0.66
        cam.azimuth = 135
        cam.elevation = -20

    print(f"{'pose':10s} {'settled q1,q2':>16s} {'arm1 z':>7s} {'arm2 z':>7s}  contacts")
    for pose in POSES:
        env.reset(options={"pose": pose})
        q = env.target.copy()
        z1 = body_min_z(m, d, arm_bids[0])
        z2 = body_min_z(m, d, arm_bids[1])
        cons = floor_contacts(m, d)
        print(f"{pose:10s} {np.round(q, 3)!s:>16s} {z1:7.4f} {z2:7.4f}  {cons}")
        if renderer is not None:
            renderer.update_scene(d, camera=cam)
            tiles.append(renderer.render().copy())
    if renderer is not None:
        renderer.close()

    print()
    for pose in POSES:
        obs, _ = env.reset(options={"pose": pose})
        up_vec = d.xmat[env.foot_body_id].reshape(3, 3)[2]
        actual = pose_from_up(float(up_vec[0]), float(up_vec[1]))
        seq = np.asarray(SEQUENCES_V1[actual], dtype=float)
        ex = GetupExecutor(actual, q0=env.target.copy())
        ex.sequence = seq
        ex.support = seq[-2]
        min_upz = 1.0
        info = {}
        for _ in range(700):
            obs, _, term, trunc, info = env.step(ex.action(env, obs))
            min_upz = min(min_upz, float(info["upright"]))
            if term or trunc:
                break
        ok = bool(info.get("goal_pose")) and int(info.get("success_count", 0)) >= 50
        print(f"{pose:10s} -> {actual:10s} ok={ok!s:5s} steps={env.step_count:3d} "
              f"up={info.get('upright', -9):+.2f} min_up={min_upz:+.2f} "
              f"q_end={np.round(info.get('servo_angles', []), 2).tolist()} "
              f"switches={ex.switches}")

    if args.out and tiles:
        save_png(args.out, montage(tiles))
        print("saved", args.out)


def montage(tiles):
    h, w, _ = tiles[0].shape
    grid = np.zeros((2 * h, 2 * w, 3), dtype=np.uint8)
    for i, t in enumerate(tiles):
        grid[(i // 2) * h:(i // 2 + 1) * h, (i % 2) * w:(i % 2 + 1) * w] = t
    return grid


def save_png(path, rgb):
    import struct
    import zlib
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(png)


if __name__ == "__main__":
    main()
