"""Render a trained self-righting policy (or random actions) in the MuJoCo viewer.

Examples (from the repository root):
  python -m training.b_line.play --model training/b_line/models/ppo_selfrising/final.zip
  python -m training.b_line.play --model training/b_line/models/ppo_selfrising/final.zip --pose pitch_pos
  python -m training.b_line.play --random --episodes 2

Behaviour by default:
  1. the policy gets the robot up;
  2. once it has stood quietly for 1 s, the stand-homing controller ramps the
     arm targets to zero (arm vertical, the assembly pose) and holds them;
  3. the viewer keeps the robot standing until the window is closed.

Use --no-home to skip the homing, and --no-hold to reset and replay episodes.

Note: MuJoCo's viewer opens a desktop window. If it fails in your terminal,
run the same command from a normal PowerShell/Command Prompt window.
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import mujoco
import numpy as np
from stable_baselines3 import PPO

from .selfright_env import POSE_RP, SelfRightEnv
from .stand_homer import FallGate, PushStand, StandHomer
from .two_policy import TwoPolicy


def viewer_running(env) -> bool:
    return env._viewer is None or env._viewer.is_running()


def apply_mouse_perturbation(env) -> None:
    """Apply the viewer's mouse-spring force for this control step.

    In passive mode the viewer only updates its MjvPerturb struct; the user's
    loop must turn it into forces. Ctrl+right-drag (vertical) and
    Ctrl+Shift+right-drag (horizontal) drag a spring on the selected body.
    """
    if env._viewer is None:
        return
    env.data.xfrc_applied[:] = 0.0
    mujoco.mjv_applyPerturbForce(env.model, env.data, env._viewer.perturb)


def main():
    p = argparse.ArgumentParser(description="Render a self-righting policy in MuJoCo")
    p.add_argument("--model", default="training/b_line/models/ppo_selfrising_sr5/final.zip")
    p.add_argument("--robot", default="selfrising_sr5")
    p.add_argument("--episodes", type=int, default=1,
                   help="number of episodes; 0 = loop until the window is closed")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--pose", choices=sorted(POSE_RP), default=None,
                   help="start from this fallen pose instead of a random one")
    p.add_argument("--upright", action="store_true",
                   help="start standing (push it with Ctrl+Shift+right-drag)")
    p.add_argument("--random", action="store_true", help="use random actions instead of a policy")
    p.add_argument("--home", dest="home", action="store_true", default=True,
                   help="after standing, ramp the arm to the vertical pose and hold (default)")
    p.add_argument("--no-home", dest="home", action="store_false",
                   help="do not home the arm after standing")
    p.add_argument("--hold", dest="hold", action="store_true", default=True,
                   help="after standing up, hold upright instead of resetting (default)")
    p.add_argument("--hold-any", action="store_true",
                   help="hold after the first episode even if not upright (for tall-chassis tests)")
    p.add_argument("--no-hold", dest="hold", action="store_false",
                   help="reset and replay episodes from fallen poses")
    p.add_argument("--no-gate", dest="gate", action="store_false", default=True,
                   help="let the policy act mid-fall (firmware default waits until fully down)")
    p.add_argument("--stand-model",
                   default="training/b_line/models/ppo_b39_ap_ft/best/best_model.zip",
                   help="arm-prop stand policy for the two-policy controller; empty disables")
    args = p.parse_args()

    # Long episodes: a full rescue (get-up + pump/push + lift-out) can take
    # ~900 control steps, so the default 600-step episode would cut it off.
    env = SelfRightEnv(robot=args.robot, render_mode="human",
                       domain_randomization=False, episode_steps=1500,
                       random_init=not args.upright, seed=args.seed)
    model = None if args.random else PPO.load(args.model, device="cpu")
    stand_model = None
    if (not args.random and args.stand_model
            and env.q_ctrl_max > env.q_half + 1e-6
            and Path(args.stand_model).exists()):
        stand_model = PPO.load(args.stand_model, device="cpu")
    two = TwoPolicy(model, stand_model) if stand_model is not None else None
    options = None if args.upright else ({"pose": args.pose} if args.pose else None)

    def next_action(obs, homer, pusher=None, gate=None, two=None):
        if gate is not None and not gate.armed:
            # Firmware parity: hold the arm until the robot is fully down.
            return (np.zeros(2, dtype=np.float64) if env.action_mode == "increment"
                    else env._prev_cmd / env.q_half)
        if two is not None:
            return two.act(obs, env)
        if pusher is not None and pusher.apply(env):
            return np.zeros(2, dtype=np.float64)
        if homer is not None and homer.state != "policy":
            return homer.action(env)
        if args.random:
            return env.action_space.sample()
        action, _ = model.predict(obs, deterministic=True)
        return action

    try:
        ep = 0
        while args.episodes <= 0 or ep < args.episodes:
            obs, info = env.reset(seed=args.seed + ep, options=options)
            # A wide-range shoulder gets the push-stand routine instead of the
            # plain home ramp: push past the arm-prop wedge, then lift out.
            pusher = (None if two is not None else
                      (PushStand() if env.q_ctrl_max > env.q_half + 1e-6 else None))
            homer = (StandHomer() if (two is None and args.home and not args.random
                                      and pusher is None) else None)
            gate = FallGate() if args.gate else None
            if two is not None:
                two.reset()
            done = False
            total = 0.0
            steps = 0
            while not done:
                if not viewer_running(env):
                    return
                action = next_action(obs, homer, pusher, gate, two)
                apply_mouse_perturbation(env)
                obs, reward, terminated, truncated, info = env.step(action)
                if gate is not None:
                    active = (two.state if two is not None else
                              pusher.state if pusher is not None else
                              (homer.state if homer is not None else None))
                    gate.update(env, info, active)
                if gate is None or gate.armed:
                    if homer is not None:
                        homer.update(env, info)
                    if pusher is not None:
                        pusher.update(env, info)
                env.render()
                time.sleep(1.0 / env.metadata["render_fps"])
                total += float(reward)
                steps += 1
                done = bool(terminated or truncated)
            print(
                f"episode {ep + 1}: reward={total:.1f} steps={steps} "
                f"up_z={info['up_z']:.2f} "
                f"tilt={math.degrees(math.acos(max(-1.0, min(1.0, info['up_z'])))):.1f}deg "
                f"settled={info['settled']} homer={homer.state if homer else '-'}"
            )
            ep += 1

            if args.hold and not args.random and (
                args.hold_any or (info["up_z"] > 0.9 and info["height_ok"])):
                print("standing; holding upright. Close the window to exit.")
                k = 0
                while viewer_running(env):
                    action = next_action(obs, homer, pusher, gate, two)
                    apply_mouse_perturbation(env)
                    obs, _, _, _, info = env.step(action)
                    if gate is not None:
                        active = (two.state if two is not None else
                                  pusher.state if pusher is not None else
                                  (homer.state if homer is not None else None))
                        gate.update(env, info, active)
                    if gate is None or gate.armed:
                        if homer is not None:
                            homer.update(env, info)
                        if pusher is not None:
                            pusher.update(env, info)
                    env.render()
                    time.sleep(1.0 / env.metadata["render_fps"])
                    k += 1
                    if k % 25 == 0:
                        print(f"hold t={k * 0.02:5.1f}s up={np.round(env._up_body(), 2)} "
                              f"q={np.round(env._prev_cmd, 2)} "
                              f"homer={homer.state if homer else '-'}", flush=True)
                return
    finally:
        env.close()


if __name__ == "__main__":
    main()
