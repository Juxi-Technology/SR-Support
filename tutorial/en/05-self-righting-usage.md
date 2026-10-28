---
title: 05 Self-Righting Usage
description: How to operate SR-Support in each fallen direction, expected motion times, serial events and monitoring logs.
---

# 05 Self-Righting Usage

## 5.1 Procedure

1. Power up with the robot upright and wait for `autorun on: get-up waits for a fall`;
2. Knock the robot over in any direction, **release it and keep it still for about 0.5 s**;
3. When `getup start pose=<pose>` appears, the executor starts automatically;
4. On success the firmware prints `standing -> executor done` and returns to standby;
5. If a run exceeds 14 s the firmware prints `executor timeout`; after a 1.5 s cooldown the
   fall gate re-triggers and retries.

## 5.2 Expected behavior per direction

| Pose | Mechanism | Real-robot time |
|---|---|---|
| `pitch_neg` (top → −X) | Elbow plants, shoulder stroke levers the body up | ~3 s |
| `pitch_pos` (top → +X) | Same lift; if it tips over during retract, the pose re-plan runs `pitch_pos` again | ~5–6 s |
| `roll_pos` (top → −Y) | Direct shoulder lever using the long travel side | ~3 s |
| `roll_neg` (top → +Y) | Arm swings over the top and holds; the body rolls over its long axis, then the re-plan hands over to the pitch lift | 5–14 s |

> The roll-then-lift behavior of `roll_neg` is the **normal working mechanism**, not a fault: the
> shoulder has only 61° of reverse travel and cannot plant on the far side of the body, so the
> robot must roll over the top first. The serial log shows
> `executor re-plan roll_neg -> pitch_pos` (or `pitch_neg`) events, 1–3 per run.

## 5.3 Executor logic (in firmware)

- 20 ticks (0.4 s) per reference waypoint, linear interpolation; output slew limit 0.08 rad/tick;
- After the waypoints, retract the arm to neutral at 0.033 rad/tick;
- Done when `up_z > 0.95` with the target at zero for 50 ticks;
- If the body settles on another lying axis (`up_z<0.6`, `|ω|<0.8` for 15 ticks), retract to
  neutral and switch to the new pose's reference (up to 5 switches).

## 5.4 Monitoring and logs

```bash
.venv-pio/Scripts/python.exe tools/hw_monitor.py COM27
```

- Appends events and 5-second telemetry summaries to `logs/hw_monitor.log`;
- Records `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost`, etc.;
- Checks the servo envelope (shoulder `[-1.07,+2.07]`, elbow `±1.55`) and writes `!! VIOLATION`;
- While the executor runs it prints a trace every 0.2 s:

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Field | Meaning |
|---|---|
| `pose` | Current reference pose |
| `ph` / `tick` | Waypoint phase / tick within the phase |
| `tgt` | Target joint angles |
| `up` | Current up vector |
| `q` | Current joint command |
| `sw` | Number of pose switches so far |

> Opening the monitor resets the ESP32; close it before flashing.

## 5.5 Record keeping

For every test record the pose, whether it ended with `done`, the duration, the number of
switches and any violations. `logs/hw_monitor.log` is the authoritative record.
