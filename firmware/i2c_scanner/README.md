# i2c_scanner — IMU 地址/接线诊断

B 线 IMU 不识别时先用这个 sketch，确认 I²C 总线上有没有设备、地址是不是 `0x23`。

## 接线

| IMU | 接到 |
|---|---|
| VCC | ESP32 **3V3**（不要接舵机 V+ 6V） |
| GND | CH3/CH4 GND 或 ESP32 GND |
| SDA | CH3 信号（GPIO6） |
| SCL | CH4 信号（GPIO7） |

## 烧录/查看

```bash
pio run -d firmware/i2c_scanner -t upload --upload-port COMx
```

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COMx
```

预期：

```
I2C scanner: SDA=GPIO6 SCL=GPIO7 @100kHz
scan...
  found 0x23
```

- 找到 `0x23`：IMU 正常，重新烧回 B 线固件。
- 找到 `0x68/0x69`：可能是 MPU6050 类模块，不是当前 B 线固件支持的 Juxi 模块。
- 什么都没有：查 3.3V、GND、SDA/SCL 是否接反、CH3/CH4 信号是否真的到 GPIO6/7、模块是否被 6V 损坏。  
- **VCC 必须接 3V3，不是 5V5，更不是 6V**；接错 5V 可能让模块不亮/损坏。
