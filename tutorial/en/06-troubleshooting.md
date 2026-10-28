---
title: 06 Troubleshooting
description: Common SR-Support symptoms, causes and fixes covering IMU, serial port, fall gate and executor timeouts.
---

# 06 Troubleshooting

## 6.1 Common symptoms

| Symptom | Likely cause | Fix |
|---|---|---|
| `waiting for IMU startup 5000 ms...` then `IMU not ready` | Slow IMU power-up, bad wiring, wrong address | Wait 5–10 s; check 3V3, SDA=GPIO6 / SCL=GPIO7, address 0x23 |
| Repeated `IMU lost -> bus reset + re-init` | Long or loose I²C wires | Shorten wires, re-seat joints |
| Flashing fails with `could not open port` / `Access is denied` | Serial port held by monitor/serial monitor | Close `hw_monitor.py` or the serial monitor first |
| Robot does not start after being placed | Body not still, or a hand is touching it | Release and keep still for ≥0.5 s; watch for `getup start` |
| Immediate flailing / wrong direction | Fall gate triggered mid-roll, misclassification | Place and release cleanly; retry |
| Run stops and prints `executor timeout` after 14 s | Reference did not finish | Normal fallback; automatic retry after 1.5 s; keep the log |
| Frequent `executor re-plan` events | Normal roll-over procedure for `roll_neg` | No action; check whether it ends with `done` |
| Servo buzzes / heats up | Stall or binding target | Send `x` or cut power; check limits and mechanical clearance |
| Arm hits the body during self-righting | Large shoulder motion | Check `Q_SHOULDER_MAX` and clearance; keep the 40 mm base height |

## 6.2 Safety commands

| Situation | Command |
|---|---|
| Stop motion immediately | `s` (hold last target) or `x` (detach PWM, release torque) |
| Recover after `x` | `r` to re-initialize, then power-cycle if needed |
| A joint moves the wrong way | `v` (shoulder) / `b` (elbow) sign flip |

## 6.3 Capturing a failure

Keep the corresponding part of `logs/hw_monitor.log`. The key lines are:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```
