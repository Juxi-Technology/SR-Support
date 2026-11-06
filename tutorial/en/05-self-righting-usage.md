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
| `roll_neg` (top → +Y) | **Full-travel direct press → elbow-wedge pumps ×2 → whip-slam retry if needed**; no roll-over | ~2–6 s |

> Earlier firmware rolled `roll_neg` over the top and re-planned to a pitch lift (5–14 s); the
> current build uses the mirror of the +Y press, so all four directions are symmetric and
> comparable in speed. An occasional `executor re-plan roll_neg -> ...` just means that press
> failed and the fallback retry kicked in - that is the normal safety net.

## 5.3 Executor logic (in firmware)

- 20 ticks (0.4 s) per reference waypoint, linear interpolation; output slew limit 0.08 rad/tick;
- After the waypoints, retract the arm to neutral at 0.033 rad/tick;
- Done when `up_z > 0.95` with the target at zero for 50 ticks;
- If the body settles on another lying axis (`up_z<0.6`, `|ω|<0.8` for 15 ticks), retract to
  neutral and switch to the new pose's reference (up to 5 switches);
- The `roll_neg` reference uses **per-stage adaptive holds**: press/pump stages hold while
  `up_z<0.92` up to a per-stage tick cap (press 40 / pump 30 / pump 30 / final 90); if the body
  comes upright mid-sequence the executor jumps straight to the retract so the later stages
  cannot knock the standing robot over.

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

## 5.6 WiFi: status page, provisioning and the wireless twin

Hotspot: SSID `SR-Support`, password `srsupport`, address `192.168.4.1` (`w` toggles it; on by
default at boot).

- **Status page**: join the hotspot and open `http://192.168.4.1` (phones usually pop the
  portal automatically). It refreshes every 300 ms: state, up vector and uprightness bar,
  joint commands, get-up pose/phase, Home WiFi state and the twin-stream switch. If the
  browser uses a proxy, add an exception for this address.
- **Provisioning (join the home WiFi)**: on the status page use the Home WiFi card -
  `Scan` → pick a network → enter the password → `Connect`. On success the ESP32 runs AP+STA:
  the hotspot stays up and the robot is reachable on the home LAN (the page shows its
  `Robot IP`). Credentials are stored in NVS and rejoined automatically on boot. 2.4 GHz only;
  scans/connects are refused while a get-up is running.
- **Wireless MuJoCo twin**: press `Twin ON` on the page (same as serial `d`), then:

  ```bash
  .venv/Scripts/python.exe tools/live_twin.py --tcp <Robot IP>:3333
  ```

  The window mirrors the real attitude live; the arm is held at its floor-contact angle like
  the stalled servo. The USB cable is only needed for flashing and log dumps. WiFi telemetry
  can also be recorded with `.venv/Scripts/python.exe tools/tcp_log.py`.
