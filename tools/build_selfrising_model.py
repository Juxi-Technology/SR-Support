"""Build the MuJoCo model for the user's SelfRisingRobot 3D print (PTK7452MG).

The STL parts come from the user's copy of the SelfRisingRobot 3D model:
  D:/Project/3D-Models/self-rising-robot/source/{footP,arm1P,arm2P,armhornP}.stl
and the second horn instance from output/armhornP_arm2_placed.stl.
The PTK7452MG-D mesh comes from D:/Project/3D-Models/servo-ptk7452mg/output.
Servo placements (R, t) come from data/servo_fit.json of the same 3D-model project.

The script:
  1. bakes a common recentring offset (assembly mm -> robot metres) into each
     part and writes one STL per rigid body instance,
  2. computes exact mass properties (volume, centroid, inertia) per part from
     the closed triangle mesh, scaled to the chosen part masses,
  3. aggregates foot / arm1 / arm2 and writes assets/robot_selfrising.xml.

Run from the repository root:
  .venv/Scripts/python.exe tools/build_selfrising_model.py
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = Path("D:/Project/3D-Models/self-rising-robot")
SERVO = Path("D:/Project/3D-Models/servo-ptk7452mg/output/PTK7452MG-D.stl")
OUT = ROOT / "training" / "b_line" / "assets" / "selfrising"
XML = ROOT / "training" / "b_line" / "assets" / "robot_selfrising.xml"

# Recentre the STL assembly frame: plate centre in X/Y, plate bottom at Z=0.
OFFSET_MM = np.array([-141.9, -79.0, 74.206])

# Printed part masses: solid STL volume x ~1.07 g/cm3 (PLA ~85% / PETG shell+infill).
MASS_FOOT_G = 17.8
MASS_ARM1_G = 9.7
MASS_ARM2_G = 20.0
MASS_HORN_G = 1.75          # each horn, 1.63 cm3
MASS_SERVO_G = 12.2         # PTK7452MG
MASS_ELECTRONICS_G = 22.0   # ESP32-S3 devkit + adapter + IMU + wires/screws

SERVO_FIT = json.loads((SRC / "data" / "servo_fit.json").read_text(encoding="utf-8"))


def read_stl(path: Path) -> np.ndarray:
    b = path.read_bytes()
    if b[:5].lower() == b"solid" and b"facet" in b[:1000]:
        verts = []
        for line in b.decode(errors="ignore").splitlines():
            s = line.strip()
            if s.startswith("vertex"):
                verts.append([float(x) for x in s.split()[1:4]])
        return np.asarray(verts, dtype=np.float64).reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    arr = np.frombuffer(b, dtype=np.uint8, count=n * 50, offset=84).reshape(n, 50)
    return arr[:, 12:48].copy().view("<f4").reshape(-1, 3, 3).astype(np.float64)


def write_stl(path: Path, tris: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    buf = bytearray(b"SR-Support self-rising robot".ljust(80, b" "))
    buf += struct.pack("<I", len(tris))
    for n, tri in zip(normals, tris):
        buf += struct.pack("<3f", *n)
        for v in tri:
            buf += struct.pack("<3f", *v)
        buf += struct.pack("<H", 0)          # attribute byte count
    path.write_bytes(bytes(buf))


def mass_props(tris: np.ndarray, mass: float):
    """Return (volume_m3, centroid_m, inertia_about_com_kgm2) for uniform density."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    vol_t = vol6 / 6.0
    vol = float(vol_t.sum())
    if vol < 0:
        vol_t = -vol_t
        vol = -vol
    if vol <= 0:
        raise ValueError("mesh is not a closed solid")

    # signed tetrahedra (origin, a, b, c)
    m1 = (a + b + c) / 4.0
    c_ = (m1 * vol_t[:, None]).sum(axis=0) / vol

    # S_ij = integral r_i r_j dV
    s = a + b + c
    S = np.empty((3, 3))
    for i in range(3):
        for j in range(3):
            per_tet = (
                a[:, i] * a[:, j]
                + b[:, i] * b[:, j]
                + c[:, i] * c[:, j]
                + s[:, i] * s[:, j]
            )
            S[i, j] = float((vol_t * per_tet / 20.0).sum())

    rho = mass / vol
    I0 = rho * (np.trace(S) * np.eye(3) - S)
    d = c_
    Ic = I0 - mass * ((d @ d) * np.eye(3) - np.outer(d, d))
    return vol, c_, Ic


def quat_from_matrix(R: np.ndarray) -> np.ndarray:
    """Rotation matrix -> (w, x, y, z)."""
    t = np.trace(R)
    if t > 0:
        w = math.sqrt(t + 1.0) / 2.0
        x = (R[2, 1] - R[1, 2]) / (4 * w)
        y = (R[0, 2] - R[2, 0]) / (4 * w)
        z = (R[1, 0] - R[0, 1]) / (4 * w)
    else:
        i = int(np.argmax(np.diag(R)))
        j, k = (i + 1) % 3, (i + 2) % 3
        q = math.sqrt(1.0 + R[i, i] - R[j, j] - R[k, k]) / 2.0
        w = (R[k, j] - R[j, k]) / (4 * q)
        qv = [0.0, 0.0, 0.0]
        qv[i] = q
        qv[j] = (R[j, i] + R[i, j]) / (4 * q)
        qv[k] = (R[k, i] + R[i, k]) / (4 * q)
        x, y, z = qv
    return np.array([w, x, y, z])


def place(tris: np.ndarray, R: np.ndarray, t_mm: np.ndarray) -> np.ndarray:
    """Apply assembly placement (mm) and the common recentring offset."""
    v = tris.reshape(-1, 3) @ R.T + (t_mm - OFFSET_MM)
    return (v * 0.001).reshape(-1, 3, 3)


def recentred(tris: np.ndarray) -> np.ndarray:
    return ((tris.reshape(-1, 3) - OFFSET_MM) * 0.001).reshape(-1, 3, 3)


def aggregate(parts):
    """parts: list of (mass, com, inertia). Returns total mass, com, inertia."""
    m = sum(p[0] for p in parts)
    c = sum(p[0] * p[1] for p in parts) / m
    I = np.zeros((3, 3))
    for mi, ci, Ii in parts:
        d = ci - c
        I += Ii + mi * ((d @ d) * np.eye(3) - np.outer(d, d))
    return m, c, I


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    def ident_place(tris):
        return recentred(tris)

    specs = [
        # name, file, mass g, body, transform
        ("foot", SRC / "source/footP.stl", MASS_FOOT_G, "foot", ident_place),
        ("arm1", SRC / "source/arm1P.stl", MASS_ARM1_G, "arm1", ident_place),
        ("arm2", SRC / "source/arm2P.stl", MASS_ARM2_G, "arm2", ident_place),
        ("horn1", SRC / "source/armhornP.stl", MASS_HORN_G, "arm1", ident_place),
        ("horn2", SRC / "output/armhornP_arm2_placed.stl", MASS_HORN_G, "arm2", ident_place),
    ]
    for name in ("servo_shoulder", "servo_elbow"):
        p = SERVO_FIT["placements"][name]
        R = np.asarray(p["R"], dtype=np.float64)
        t = np.asarray(p["t"], dtype=np.float64)
        assert np.allclose(R @ R.T, np.eye(3), atol=1e-6), f"{name} R not orthonormal"
        assert abs(np.linalg.det(R) - 1.0) < 1e-6, f"{name} det(R) != 1"
        body = "foot" if name == "servo_shoulder" else "arm1"
        mesh = "servo1" if name == "servo_shoulder" else "servo2"
        specs.append((mesh, SERVO, MASS_SERVO_G, body,
                      lambda tris, R=R, t=t: place(tris, R, t)))

    parts = []
    for name, path, mass_g, body, xf in specs:
        tris = xf(read_stl(path))
        write_stl(OUT / f"{name}.stl", tris)
        vol, com, I = mass_props(tris, mass_g * 1e-3)
        parts.append(dict(name=name, body=body, mass=mass_g * 1e-3, com=com, inertia=I,
                          volume_cm3=vol * 1e6))
        print(f"{name:14s} body={body:6s} vol={vol*1e6:6.2f} cm3 "
              f"mass={mass_g:5.1f} g com={np.round(com*1000, 2)} mm")

    # Electronics box (ESP32-S3 + adapter + IMU + screws) on the base plate.
    elec_mass = MASS_ELECTRONICS_G * 1e-3
    elec_half = np.array([0.026, 0.013, 0.009])      # 52 x 26 x 18 mm
    elec_pos = np.array([0.0, -0.024, 0.012])
    a, b, c = elec_half
    Ie = elec_mass / 3.0 * np.diag([b * b + c * c, a * a + c * c, a * a + b * b])
    parts.append(dict(name="electronics", body="foot", mass=elec_mass,
                      com=elec_pos, inertia=Ie, volume_cm3=float("nan")))
    print(f"{'electronics':14s} body=foot   box=52x26x18 mm mass={MASS_ELECTRONICS_G:.1f} g "
          f"com={np.round(elec_pos*1000, 2)} mm")

    bodies = {}
    for body in ("foot", "arm1", "arm2"):
        m, c, I = aggregate([(p["mass"], p["com"], p["inertia"]) for p in parts
                             if p["body"] == body])
        bodies[body] = (m, c, I)
        print(f"BODY {body:5s} mass={m*1e3:6.2f} g com={np.round(c*1000, 2)} mm")

    total = sum(b[0] for b in bodies.values())
    print(f"TOTAL mass = {total*1e3:.1f} g")

    def inertial(body):
        m, c, I = bodies[body]
        return (f'<inertial pos="{c[0]:.6f} {c[1]:.6f} {c[2]:.6f}" mass="{m:.6f}"\n'
                f'                  fullinertia="{I[0,0]:.9e} {I[1,1]:.9e} {I[2,2]:.9e} '
                f'{I[0,1]:.9e} {I[0,2]:.9e} {I[1,2]:.9e}"/>')

    xml = f"""<mujoco model="selfrising_ptk7452">
  <!-- SR-Support B-line, geometry of the user's SelfRisingRobot 3D print.
       STL source: D:/Project/3D-Models/self-rising-robot/source (no license;
       internal use only, do not redistribute). Servo placement from
       data/servo_fit.json (PTK7452MG-D). Generated by
       tools/build_selfrising_model.py - do not edit by hand. -->
  <compiler angle="radian" meshdir="selfrising" autolimits="true"/>
  <option timestep="0.001" integrator="implicitfast" cone="elliptic" impratio="10"/>

  <default>
    <geom friction="0.9 0.02 0.001" solref="0.004 1" solimp="0.95 0.99 0.001"
          contype="2" conaffinity="0"/>
    <joint type="hinge" limited="true" range="-1.55 1.55" damping="0.02" armature="0.0001"/>
    <position ctrllimited="true" ctrlrange="-1.55 1.55" forcelimited="true"
              forcerange="-0.333 0.333" kp="50.0" kv="0.5"/>
  </default>

  <asset>
    <mesh name="foot" file="foot.stl"/>
    <mesh name="arm1" file="arm1.stl"/>
    <mesh name="arm2" file="arm2.stl"/>
    <mesh name="horn1" file="horn1.stl"/>
    <mesh name="horn2" file="horn2.stl"/>
    <mesh name="servo1" file="servo1.stl"/>
    <mesh name="servo2" file="servo2.stl"/>
  </asset>

  <worldbody>
    <light name="top" pos="0 0 0.8" dir="0 0 -1" directional="true"/>
    <geom name="floor" type="plane" size="1 1 0.05" contype="1" conaffinity="3"
          friction="1.2 0.02 0.001" rgba="0.55 0.58 0.62 1"/>

    <body name="foot" pos="0 0 0">
      <freejoint name="root"/>
      {inertial('foot')}
      <geom type="mesh" mesh="foot" rgba="0.75 0.22 0.25 1"/>
      <geom type="mesh" mesh="servo1" rgba="0.35 0.35 0.35 1"/>
      <geom name="foot_plate" type="box" pos="0 0 0.0015" size="0.030 0.03645 0.0015"
            friction="0.9 0.02 0.001" rgba="0 0 0 0"/>
      <geom name="foot_tower" type="box" pos="0.00255 0 0.01955" size="0.00945 0.0059 0.01695"
            rgba="0 0 0 0"/>
      <geom name="electronics" type="box" pos="0 -0.024 0.012" size="0.026 0.013 0.009"
            rgba="0.15 0.15 0.15 1"/>

      <body name="arm1" pos="0 0 0">
        <joint name="servo1_joint" axis="1 0 0" pos="0.0199 0 0.0254"/>
        {inertial('arm1')}
        <geom type="mesh" mesh="arm1" rgba="0.20 0.45 0.80 1"/>
        <geom type="mesh" mesh="servo2" rgba="0.35 0.35 0.35 1"/>
        <geom name="arm1_lower" type="box" pos="0.0025 0 0.0251" size="0.0199 0.0060 0.0059"
              rgba="0 0 0 0"/>
        <geom name="arm1_upper" type="box" pos="0 0.0081 0.0536" size="0.00625 0.0143 0.0280"
              rgba="0 0 0 0"/>
        <geom type="mesh" mesh="horn1" rgba="0.20 0.55 0.30 1"/>

        <body name="arm2" pos="0 0 0">
          <joint name="servo2_joint" axis="0 1 0" pos="0 0.0199 0.0704"/>
          {inertial('arm2')}
          <geom type="mesh" mesh="arm2" rgba="0.95 0.50 0.10 1"/>
          <geom type="mesh" mesh="horn2" rgba="0.20 0.55 0.30 1"/>
          <geom name="arm2_crossbar" type="box" pos="0 0.0025 0.0905"
                size="0.00625 0.0199 0.0035" rgba="0 0 0 0"/>
          <!-- arm2_bar: the printed bar is centred on y=0 (slicing arm2.stl at
               z=0.11..0.165 gives y in [-7.2, +7.2] mm); keep the proxy there. -->
          <geom name="arm2_bar" type="box" pos="0 0 0.1309"
                size="0.00625 0.0072 0.0371" friction="1.2 0.02 0.001" rgba="0 0 0 0"/>
        </body>
      </body>
    </body>
  </worldbody>

  <actuator>
    <position name="servo1" joint="servo1_joint"/>
    <position name="servo2" joint="servo2_joint"/>
  </actuator>
</mujoco>
"""
    XML.write_text(xml, encoding="utf-8")
    print("wrote", XML)

    params = {
        "offset_mm": OFFSET_MM.tolist(),
        "bodies": {k: {"mass_g": v[0] * 1e3, "com_mm": (v[1] * 1e3).tolist(),
                       "inertia": v[2].tolist()} for k, v in bodies.items()},
        "parts": [{k: (v.tolist() if isinstance(v, np.ndarray) else v)
                   for k, v in p.items()} for p in parts],
    }
    (OUT / "model_params.json").write_text(json.dumps(params, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
