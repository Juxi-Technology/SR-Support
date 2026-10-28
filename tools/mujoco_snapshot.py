"""Render off-screen MuJoCo snapshots of the B-line model to PNG (no GUI).

Uses mujoco.Renderer plus a tiny zlib-based PNG writer, so it works without
Pillow / imageio / matplotlib.

Examples (from the repository root):
  .venv/Scripts/python.exe tools/mujoco_snapshot.py
  .venv/Scripts/python.exe tools/mujoco_snapshot.py --episode-step 120
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "training" / "b_line" / "assets" / "robot_selfrising.xml"
sys.path.insert(0, str(ROOT))


def write_png(path: Path, rgb: np.ndarray) -> None:
    """Write an (H, W, 3) uint8 array as a PNG using only the stdlib."""
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        payload = tag + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


POSE_RP = {
    "upright": (0.0, 0.0),
    "roll_pos": (np.pi / 2.0, 0.0),
    "roll_neg": (-np.pi / 2.0, 0.0),
    "pitch_pos": (0.0, np.pi / 2.0),
    "pitch_neg": (0.0, -np.pi / 2.0),
}


def roll_pitch_quat(roll: float, pitch: float) -> np.ndarray:
    cr, sr = np.cos(roll / 2.0), np.sin(roll / 2.0)
    cp, sp = np.cos(pitch / 2.0), np.sin(pitch / 2.0)
    return np.array([cr * cp, sr * cp, cr * sp, -sr * sp])


def main() -> None:
    p = argparse.ArgumentParser(description="Render B-line MuJoCo snapshots")
    p.add_argument("--out", default="training/b_line/snapshots")
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--episode-step", type=int, default=-1,
                   help="also render the model after N env steps with random actions")
    p.add_argument("--strip", action="store_true",
                   help="render an 8-frame strip of a random-action episode")
    p.add_argument("--policy", default=None,
                   help="render an 8-frame strip of this SB3 policy (e.g. models/.../final.zip)")
    p.add_argument("--no-home", action="store_true",
                   help="disable the stand-homing controller in the policy strip")
    p.add_argument("--robot", default="selfrising")
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    torso = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "torso")
    frames = []

    with mujoco.Renderer(model, args.height, args.width) as renderer:
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(cam)
        cam.lookat[:] = (0.0, 0.0, 0.075)
        cam.distance = 0.40
        cam.elevation = -16.0
        cam.azimuth = 135.0

        for name, (roll, pitch) in POSE_RP.items():
            mujoco.mj_resetData(model, data)
            data.qpos[0:3] = (0.0, 0.0, 0.08)
            data.qpos[3:7] = roll_pitch_quat(roll, pitch)
            data.ctrl[:] = 0.0
            mujoco.mj_forward(model, data)
            for _ in range(400):          # settle on the floor
                data.ctrl[:] = 0.0
                mujoco.mj_step(model, data)
            renderer.update_scene(data, camera=cam)
            img = renderer.render()
            write_png(out / f"{name}.png", np.ascontiguousarray(img))
            frames.append(img)
            print(f"{name:10s} up_z={data.xmat[torso].reshape(3, 3)[2, 2]:+.3f}")

        if args.policy:
            from stable_baselines3 import PPO

            from training.b_line.selfright_env import SelfRightEnv
            from training.b_line.stand_homer import StandHomer

            env = SelfRightEnv(robot=args.robot, domain_randomization=False, seed=2)
            model = PPO.load(args.policy, device="cpu")
            homer = None if args.no_home else StandHomer()
            obs, _ = env.reset(seed=2, options={"pose": "pitch_pos"})
            strip = []
            for i in range(400):
                if homer is not None and homer.state != "policy":
                    action = homer.action(env)
                else:
                    action, _ = model.predict(obs, deterministic=True)
                obs, _, _, _, info = env.step(action)
                if homer is not None:
                    homer.update(env, info)
                if (i + 1) % 50 == 0:
                    renderer.update_scene(env.data, camera=cam)
                    strip.append(renderer.render())
            write_png(out / "policy_strip.png",
                      np.ascontiguousarray(np.concatenate(strip, axis=1)))
            print(f"wrote {out / 'policy_strip.png'}  final up_z={info['up_z']:+.3f} "
                  f"settled={info['settled']} homer={homer.state if homer else '-'}")
            env.close()

        if args.strip:
            from training.b_line.selfright_env import SelfRightEnv

            env = SelfRightEnv(robot="selfrising", domain_randomization=False, seed=1)
            env.reset(seed=1, options={"pose": "pitch_pos"})
            rng = np.random.default_rng(1)
            strip = []
            for i in range(8 * 25):          # 25 control steps (0.5 s) per frame
                env.step(rng.uniform(-1.0, 1.0, 2))
                if (i + 1) % 25 == 0:
                    renderer.update_scene(env.data, camera=cam)
                    strip.append(renderer.render())
            write_png(out / "strip.png",
                      np.ascontiguousarray(np.concatenate(strip, axis=1)))
            print("wrote", out / "strip.png")
            env.close()

        if args.episode_step >= 0:
            from training.b_line.selfright_env import SelfRightEnv

            env = SelfRightEnv(robot="selfrising", domain_randomization=False, seed=0)
            env.reset(seed=0, options={"pose": "pitch_pos"})
            rng = np.random.default_rng(0)
            for _ in range(args.episode_step):
                env.step(rng.uniform(-1.0, 1.0, 2))
            renderer.update_scene(env.data, camera=cam)
            img = renderer.render()
            write_png(out / f"random_{args.episode_step}steps.png", np.ascontiguousarray(img))
            frames.append(img)
            print(f"random {args.episode_step} steps up_z="
                  f"{env.data.xmat[torso].reshape(3, 3)[2, 2]:+.3f}")
            env.close()

    per_row = 3
    rows = []
    for start in range(0, len(frames), per_row):
        row = frames[start:start + per_row]
        while len(row) < per_row:
            row.append(np.zeros_like(frames[0]))
        rows.append(np.concatenate(row, axis=1))
    write_png(out / "montage.png", np.ascontiguousarray(np.concatenate(rows, axis=0)))
    print("wrote", out / "montage.png")


if __name__ == "__main__":
    main()
