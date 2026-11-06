# servo_test_ptk — 舵机信号/方向测试

| 舵机 | 信号 | 转接板 |
|---|---|---|
| 肩 | GPIO4 | CH1 信号 |
| 肘 | GPIO5 | CH2 信号 |
| V+ | 6V/5A | CH1/CH2 V+ |
| GND | 电源 − / ESP32 GND | 共地 |

上电只输出 **1520 µs 中位**，不自动动；串口命令：

| 命令 | 作用 |
|---|---|
| `1` / `2` | 选肩/肘 |
| `+` / `-` | 选中舵机 ±10 µs |
| `t` | 选中舵机慢速 ±0.35 rad 扫动 |
| `c` | 两个回中 |
| `p` | 打印状态 |

```bash
pio run -d firmware/servo_test_ptk -t upload --upload-port COMx
```

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COMx
```

> 测试时清空关节扫掠面、手扶底座；异常立即断 6V。  
> 这只是测试固件；确认方向和机械后，再烧回 `sr_support_b_ptk`。
