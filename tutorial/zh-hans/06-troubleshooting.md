---
title: 06 故障排查
description: SR-Support 自扶正装置常见现象、原因与处理方法（IMU、串口、跌倒门、执行器超时等）。
---

# 06 故障排查

## 6.1 常见现象

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 串口显示 `waiting for IMU startup 5000 ms...` 后 `IMU not ready` | IMU 上电慢、接线不良、地址不对 | 等待 5–10 s；检查 3V3 供电、SDA=GPIO6 / SCL=GPIO7、地址 0x23 |
| `IMU lost -> bus reset + re-init` 反复出现 | I²C 线过长、接触不良 | 缩短 I²C 线、检查焊接/杜邦头 |
| 烧录报 `could not open port` / `Access is denied` | 串口被监控或监视器占用 | 先关闭 `hw_monitor.py` / 串口监视器再烧录 |
| 放倒后长时间不动 | 身体未静止或手仍扶着 | 松手并保持静止 ≥0.5 s；观察 `getup start` 事件 |
| 放倒后立即乱摆、方向错误 | 跌倒门在滚动中触发、姿态分类错误 | 确认摆放后静止；必要时重新放倒 |
| 执行到一半停住，14 s 后 `executor timeout` | 该姿态参考未完成 | 属正常兜底；1.5 s 后自动重试；连续失败请记录日志 |
| 频繁出现 `executor re-plan` 切换 | `roll_neg` 方向的正常滚翻过程 | 无需处理；观察最终是否 `done` |
| 舵机发出持续吱声/发热 | 堵转、目标顶死 | 立即 `x` 卸力或断电；检查关节限位与机械干涉 |
| 扶正时手臂扫到机身 | 肩部大幅动作 | 检查 `Q_SHOULDER_MAX` 与机械间隙；保持底座 40 mm 总高 |

## 6.2 安全命令

| 情况 | 命令 |
|---|---|
| 需要立即停止动作 | `s`（保持当前目标）或 `x`（释放 PWM，舵机卸力） |
| 舵机卸力后恢复 | `r` 重新初始化 → 上电/复位 |
| 动作方向反了 | `v`（肩）/ `b`（肘）翻转符号 |

## 6.3 记录失败现场

出现异常时保留 `logs/hw_monitor.log` 对应时间段，重点字段：

```text
<时间> getup start pose=... up=(x,y,z)
<时间> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<时间> executor re-plan A -> B up=(x,y,z)
<时间> standing -> executor done | executor timeout
```
