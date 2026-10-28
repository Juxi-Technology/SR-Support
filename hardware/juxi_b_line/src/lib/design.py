"""Parametric structure for the 2R self-righting robot.

Units: millimetres. Frame: base bottom centre at the origin, +Z up.
The 2R arm is: shoulder servo (shaft along +X) -> upper arm -> elbow servo
(shaft along +Y) -> forearm -> rubber pad.

The CAD is an independent reconstruction of the published poco/SelfRisingRobot
architecture (no license on that repo; geometry here is ours). Servo pockets
are sized from published case dimensions; verify tab/horn geometry with the
actual servos before printing.
"""

from __future__ import annotations

from dataclasses import dataclass

from cadgen import build123d as bd

# Juxi ICM42670P IMU carrier: 42.5 x 30 mm board. It sits flat in the -Y
# side of the electronics bay, +X forward (USB-C toward the rear), +Z up.
IMU_BOARD_L = 42.5
IMU_BOARD_W = 30.0
IMU_TRAY_GAP = 0.2
IMU_RAIL_T = 0.8
IMU_RAIL_H = 4.0


@dataclass(frozen=True)
class ServoSpec:
    name: str
    length: float   # case long axis
    width: float    # case thickness
    height: float   # shaft axis / overall height
    horn_radius: float
    horn_screw_dz: float


@dataclass(frozen=True)
class RobotDims:
    name: str
    servo: ServoSpec
    base_w: float
    base_d: float
    base_h: float
    wall: float
    floor: float
    tower: float
    tower_corner: float
    plate_corner: float
    shoulder_z: float
    arm1_len: float
    arm2_len: float
    pad_r: float
    horn_boss_len: float
    horn_boss_r: float


SCS0009 = ServoSpec(
    name="SCS0009",
    length=23.2,
    width=12.1,
    height=25.25,
    horn_radius=10.0,
    horn_screw_dz=5.0,
)
SG90 = ServoSpec(
    name="SG90",
    length=22.8,
    width=12.2,
    height=28.5,
    horn_radius=8.5,
    horn_screw_dz=4.5,
)
PTK7465 = ServoSpec(
    name="PTK7465MG",
    length=23.7,
    width=12.0,
    height=26.6,
    # 25T spline; horn radius and M2 spacing are assumptions to measure.
    horn_radius=10.0,
    horn_screw_dz=5.0,
)

A = RobotDims(
    name="a_scs0009",
    servo=SCS0009,
    base_w=64.0,
    base_d=96.0,
    base_h=20.0,
    wall=3.0,
    floor=4.0,
    tower=24.0,
    tower_corner=4.0,
    plate_corner=8.0,
    shoulder_z=100.0,
    arm1_len=45.0,
    arm2_len=100.0,
    pad_r=12.0,
    horn_boss_len=6.0,
    horn_boss_r=10.0,
)
B = RobotDims(
    name="b_ptk7465",
    servo=PTK7465,
    base_w=56.0,
    base_d=92.0,
    base_h=16.0,
    wall=2.5,
    floor=3.0,
    tower=20.0,
    tower_corner=3.0,
    plate_corner=6.0,
    shoulder_z=80.0,
    arm1_len=45.0,
    arm2_len=100.0,
    pad_r=10.0,
    horn_boss_len=5.0,
    horn_boss_r=8.5,
)


def _imu_center_y(d: RobotDims) -> float:
    return -(
        d.tower / 2.0
        + IMU_TRAY_GAP
        + IMU_RAIL_T
        + IMU_TRAY_GAP
        + IMU_BOARD_W / 2.0
    )


def imu_tray(d: RobotDims) -> bd.Shape:
    """Open tray for the 42.5 x 30 mm Juxi IMU carrier.

    Two side rails set the Y position; two rear posts leave the central USB-C
    opening clear. The board is held down with VHB tape (no screw spacing is
    published for this carrier).
    """
    cy = _imu_center_y(d)
    rail_y = IMU_BOARD_W / 2.0 + IMU_TRAY_GAP + IMU_RAIL_T / 2.0
    length = IMU_BOARD_L + 1.5
    tray = None
    for sign in (-1.0, 1.0):
        rail = bd.Pos(0, cy + sign * rail_y, d.floor + IMU_RAIL_H / 2.0) * bd.Box(
            length, IMU_RAIL_T, IMU_RAIL_H
        )
        tray = rail if tray is None else tray + rail
        stop = bd.Pos(
            -length / 2.0 + 0.15,
            cy + sign * (IMU_BOARD_W / 2.0 - 2.0),
            d.floor + IMU_RAIL_H / 2.0,
        ) * bd.Box(1.0, 2.0, IMU_RAIL_H)
        tray += stop
    return tray


def _x_cyl(r: float, length: float) -> bd.Shape:
    return bd.Rot(0, 90, 0) * bd.Cylinder(r, length)


def _y_cyl(r: float, length: float) -> bd.Shape:
    return bd.Rot(90, 0, 0) * bd.Cylinder(r, length)


# ------------------------------------------------------------------------- base
def base_part(d: RobotDims) -> bd.Shape:
    s = d.servo
    plate = bd.extrude(
        bd.RectangleRounded(d.base_w, d.base_d, d.plate_corner), amount=d.base_h
    )
    # Hollow electronics/battery bay, open at the top.
    bay = bd.Pos(0, 0, d.floor) * bd.extrude(
        bd.RectangleRounded(
            d.base_w - 2 * d.wall, d.base_d - 2 * d.wall, d.plate_corner - d.wall
        ),
        amount=d.base_h - d.floor + 1.0,
    )
    body = plate - bay

    # Central tower up to the shoulder.
    tower_h = d.shoulder_z - d.base_h
    tower = bd.Pos(0, 0, 0) * bd.extrude(
        bd.RectangleRounded(d.tower, d.tower, d.tower_corner), amount=d.shoulder_z
    )
    body += tower

    # Shoulder servo cradle: open toward +X (horn side), back wall at -X.
    x0 = -(s.height / 2 + 3.0)
    x1 = s.height / 2
    yw = s.width / 2 + 3.0
    zw = s.length / 2 + 3.0
    cradle = bd.Pos((x0 + x1) / 2, 0, d.shoulder_z) * bd.Box(
        x1 - x0, 2 * yw, 2 * zw
    )
    body += cradle
    cut_x0 = -(s.height / 2 + 0.5)
    cut_x1 = s.height / 2 + 8.0
    pocket = bd.Pos((cut_x0 + cut_x1) / 2, 0, d.shoulder_z) * bd.Box(
        cut_x1 - cut_x0, s.width + 0.8, s.length + 0.8
    )
    body -= pocket

    # Zip-tie slots over the servo.
    for dz in (-zw * 0.45, zw * 0.45):
        body -= bd.Pos((x0 + x1) / 2, 0, d.shoulder_z + dz + zw - 1.0) * bd.Box(
            x1 - x0 + 2.0, 4.0, 2.0
        )

    # USB-C / power opening in the +X wall.
    body -= bd.Pos(d.base_w / 2 - 0.5, 0, d.base_h * 0.4) * bd.Box(7.0, 14.0, 5.0)

    # MCU standoffs in the +Y bay (board sits above the bay floor).
    sx = min(d.base_w * 0.18, 10.0)
    sy = (d.base_d / 2 + d.tower / 2) / 2
    for x in (-sx, sx):
        for y in (sy - 6.0, sy + 6.0):
            post = bd.Pos(x, y, d.floor) * bd.Cylinder(2.8, 5.0)
            hole = bd.Pos(x, y, d.floor) * bd.Cylinder(1.1, 6.0)
            body += post - hole

    # IMU tray on the -Y side of the bay, below the rim.
    body += imu_tray(d)

    body.label = f"{d.name}_base"
    return body


# ------------------------------------------------------------------------ arm1
def arm1_part(d: RobotDims) -> bd.Shape:
    s = d.servo
    plate_x = s.height / 2 + 0.5
    plate_t = d.horn_boss_len
    boss_c = plate_x + plate_t / 2
    boss = bd.Pos(boss_c, 0, 0) * _x_cyl(d.horn_boss_r, plate_t)
    boss -= bd.Pos(boss_c, 0, 0) * _x_cyl(2.2, plate_t + 2.0)
    for dz in (-s.horn_screw_dz / 2, s.horn_screw_dz / 2):
        boss -= bd.Pos(boss_c, 0, dz) * _x_cyl(1.1, plate_t + 2.0)

    # Vertical limb starts above the servo horn so it cannot fill the recess.
    plate_z0 = max(d.horn_boss_r - 1.0, 6.0)
    plate_h = d.arm1_len - plate_z0
    plate = bd.Pos(boss_c, 0, plate_z0 + plate_h / 2) * bd.Box(
        plate_t, 20.0, plate_h
    )
    # Shelf that carries the elbow cradle back to the joint axis.
    shelf = bd.Pos((boss_c - 8.0) / 2, 0, d.arm1_len - 3.0) * bd.Box(
        boss_c + 8.0, 20.0, 6.0
    )
    body = boss + plate + shelf
    # Recess after fusing so the plate cannot fill it.
    body -= bd.Pos(plate_x + 2.0, 0, 0) * _x_cyl(max(d.horn_boss_r - 1.0, 5.0), 4.0)

    # Elbow servo cradle, pocket open along Y; the forearm fork rotates outside.
    cx = s.width / 2 + 2.0
    cy = s.height / 2 + 2.0
    cz = s.length / 2 + 2.0
    cradle = bd.Pos(0, 0, d.arm1_len) * bd.Box(2 * cx, 2 * cy, 2 * cz)
    body += cradle
    body -= bd.Pos(0, 0, d.arm1_len) * bd.Box(
        s.width + 0.8, 2 * cy + 4.0, s.length + 0.8
    )
    # Open the +Y side of the cradle for the forearm horn hub.
    body -= bd.Pos(0, s.height / 2 + 0.2 + 5.0, d.arm1_len) * _y_cyl(
        d.horn_boss_r + 0.5, 10.0
    )
    # Zip-tie slots over the elbow servo.
    for dz in (-cz * 0.45, cz * 0.45):
        body -= bd.Pos(0, 0, d.arm1_len + dz + cz - 1.0) * bd.Box(
            2 * cx + 2.0, 4.0, 2.0
        )

    body.label = f"{d.name}_arm1"
    return body


# ------------------------------------------------------------------------ arm2
def arm2_part(d: RobotDims) -> bd.Shape:
    s = d.servo
    fork_y = s.height / 2 + 5.0
    fork_t = 4.0
    plate_h = 39.0
    plate_zc = 5.5
    # Two fork plates straddle the elbow servo; 1 mm clear of the arm1 cradle.
    left = bd.Pos(0, fork_y, plate_zc) * bd.Box(20.0, fork_t, plate_h)
    right = bd.Pos(0, -fork_y, plate_zc) * bd.Box(20.0, fork_t, plate_h)
    # Overlap the plates and the link by 1-2 mm so the union fuses.
    bridge = bd.Pos(0, 0, 27.0) * bd.Box(20.0, 2 * (fork_y + fork_t / 2), 8.0)
    # The link must sit beside the arm1 cradle, on the servo-horn side.
    link_y = fork_y + 4.0
    link_w = min(20.0, 2.0 * d.pad_r - 2.0)
    link = bd.Pos(0, link_y, (30.0 + d.arm2_len) / 2) * bd.Box(
        link_w, 6.0, d.arm2_len - 30.0
    )
    body = left + right + bridge + link

    # Horn boss on the +Y fork plate.
    boss_len = (fork_y + 2.0) - (s.height / 2 + 0.2)
    boss_c = (s.height / 2 + 0.2) + boss_len / 2
    boss = bd.Pos(0, boss_c, 0) * _y_cyl(d.horn_boss_r, boss_len)
    boss -= bd.Pos(0, boss_c, 0) * _y_cyl(2.2, boss_len + 2.0)
    for dz in (-s.horn_screw_dz / 2, s.horn_screw_dz / 2):
        boss -= bd.Pos(0, boss_c, dz) * _y_cyl(1.1, boss_len + 2.0)
    boss -= bd.Pos(0, s.height / 2 + 2.2, 0) * _y_cyl(
        max(d.horn_boss_r - 1.0, 5.0), 4.0
    )
    body += boss

    # Stub-axle hole in the -Y plate.
    body -= bd.Pos(0, -fork_y, 0) * _y_cyl(1.7, fork_t + 2.0)

    # Rubber pad at the tip: cylinder along Y with a band groove.
    pad = bd.Pos(0, link_y, d.arm2_len) * _y_cyl(d.pad_r, 20.0)
    body += pad
    groove = bd.Pos(0, link_y, d.arm2_len) * (
        bd.Rot(90, 0, 0) * bd.Torus(d.pad_r - 1.0, 1.3)
    )
    body -= groove

    body.label = f"{d.name}_arm2"
    return body


# -------------------------------------------------------------------- assembly
def assembly(d: RobotDims, base, arm1, arm2) -> bd.Compound:
    s = d.servo
    arm1_placed = bd.Pos(0, 0, d.shoulder_z) * arm1
    arm1_placed.label = f"{d.name}_arm1"
    arm2_placed = bd.Pos(0, 0, d.shoulder_z + d.arm1_len) * arm2
    arm2_placed.label = f"{d.name}_arm2"
    base.label = f"{d.name}_base"

    servo_shoulder = bd.Pos(0, 0, d.shoulder_z) * bd.Box(
        s.height, s.width, s.length
    )
    servo_shoulder.label = "servo_shoulder"
    servo_elbow = bd.Pos(0, 0, d.shoulder_z + d.arm1_len) * bd.Box(
        s.width, s.height, s.length
    )
    servo_elbow.label = "servo_elbow"

    imu_board = bd.Pos(0, _imu_center_y(d), d.floor + 0.8) * bd.Box(
        IMU_BOARD_L, IMU_BOARD_W, 1.6
    )
    imu_board.label = "imu_board"

    return bd.Compound(
        children=[
            base,
            arm1_placed,
            arm2_placed,
            servo_shoulder,
            servo_elbow,
            imu_board,
        ],
        label=f"{d.name}_assembly",
    )
