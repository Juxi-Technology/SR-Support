---
title: 09 Troubleshooting
description: Common SR-Support symptoms, causes and fixes covering IMU, serial port, fall gate, executor timeouts and WiFi.
---

# 09 Troubleshooting

Serial commands are sent through a serial assistant/monitor: type them in the send box and
press Enter (enable "send newline" in UartAssist); serial tools / the Windows UartAssist
download are on [page 03, section 3.3](./03-build-flash).

## 9.1 Common symptoms

| Symptom | Likely cause | Fix |
|---|---|---|
| `waiting for IMU startup 5000 ms...` then `IMU not ready` | Slow IMU power-up, bad wiring, wrong address | Wait 5–10 s; check 3V3, SDA=GPIO6 / SCL=GPIO7, address 0x23 |
| Repeated `IMU lost -> bus reset + re-init` | Long or loose I²C wires | Shorten wires, re-seat joints |
| Flashing fails with `could not open port` / `Access is denied` | Serial port held by monitor/serial monitor | Close `hw_monitor.py` or the serial monitor first |
| Robot does not start after being placed | Body not still, or a hand is touching it | Release and keep still for ≥0.5 s; watch for `getup start` |
| Immediate flailing / wrong direction | Fall gate triggered mid-roll, misclassification | Place and release cleanly; retry |
| Run stops and prints `executor timeout` after 14 s | Reference did not finish | Normal fallback; automatic retry after 1.5 s; keep the log |
| Occasional `executor re-plan` events | Normal fallback after a failed `roll_neg` press | Check whether it ends with `done` |
| Servo buzzes / heats up | Stall or binding target | Send `x` or cut power; check limits and mechanical clearance |
| Arm hits the body during self-righting | Large shoulder motion | Check `Q_SHOULDER_MAX` and clearance; keep the ~68 mm base height |
| `up` does not match the real pose (persistent 5°+ tilt while lying) | Accel zero offsets uncalibrated | Stand the robot level and send `c` (see [page 06, 6.2](./06-debug-and-calibrate)) |
| Arm does not rest at the visual center after retracting | Zero drifted (re-indexed/re-assembled without re-zeroing) | Re-zero with the [page 05 tool](./05-zero-tool) and bake it |
| Servo buzzes/chatters after a get-up | Analog servo transient self-excitation after large motion/stalls (output is constant) | Self-decays; add rubber damping washers or use a digital servo; pinching the arm silences it instantly |
| Status page / provisioning unreachable | Browser proxy not bypassed, or hotspot off | Add `192.168.4.1` to the proxy exceptions; send `w` to enable WiFi |

## 9.2 Safety commands

| Situation | Command |
|---|---|
| Stop motion immediately | `s` (hold last target) or `x` (detach PWM, release torque) |
| Recover after `x` | `r` to re-initialize, then power-cycle if needed |
| A joint moves the wrong way | `v` (shoulder) / `b` (elbow) sign flip |

## 9.3 Capturing a failure

Keep the corresponding part of `logs/hw_monitor.log`. The key lines are:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```
