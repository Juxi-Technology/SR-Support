/*
 * Juxi 6 轴 IMU（无 Mag/BARO）ESP32 I2C 测试固件
 * ------------------------------------------------------------------
 * 模块资料：飞书 wiki「IMU模块使用教程」及「IMU模块-串口与I2C通讯协议」
 *   - 6 轴 = 三轴加速度 + 三轴陀螺 + 板载 Mahony 融合
 *   - 无磁力计（0x10~0x15）、无气压计（0x32~0x41）：不要读这些寄存器
 *   - I2C 从机地址：0x23
 *   - I2C 时钟：100 kHz（不要用 400 kHz）
 *   - 供电：3.3V 或 5V；本示例用 3.3V，逻辑电平与 ESP32 一致
 *   - 启动时间：约 5000 ms（上电后先等 5 秒再读）
 *   - 欧拉角：寄存器 0x26~0x31，float32 小端，单位弧度
 *   - 加速度：0x04~0x09，int16 小端，缩放 16/32767 g
 *   - 陀螺仪：0x0A~0x0F，int16 小端，缩放 2000/32767 °/s
 *   - 版本号：0x01~0x03
 *
 * 接线（ESP32 DevKit V1）：
 *   IMU VCC/3V3 -> ESP32 3V3
 *   IMU GND  -> ESP32 GND
 *   IMU SDA  -> ESP32-S3 GPIO6
 *   IMU SCL  -> ESP32-S3 GPIO7
 *   IMU RX/TX 不接（本示例用 I2C）
 *
 * 输出：
 *   roll,pitch,yaw,tilt,azimuth,ax,ay,az,gx,gy,gz
 *   可直接用 Arduino Serial Plotter 看姿态。
 *
 * 注意：
 *   - 这是参考测试固件，未在实机验证。
 *   - 模块上电后 5 秒内数据可能无效；请保持静止/直立。
 *   - 欧拉角是模块内部 Mahony 融合结果；不要再用互补滤波叠加。
 *   - 6 轴的 yaw 是相对值，会漂移；只用于调试，不要用于绝对方位。
 *     倒地方位用加速度计 `atan2(ay, ax)`（本固件的 azimuth）。
 *   - 如果读数全 0 或不变，先检查地址 0x23、100kHz、共地、3.3V。
 */

#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <string.h>

// ------------------------------------------------------------------
// 配置
// ------------------------------------------------------------------
#define IMU_ADDR       0x23
#define SDA_PIN        6
#define SCL_PIN        7
#define I2C_HZ         100000

#define STARTUP_WAIT_MS 5000
#define PRINT_INTERVAL_MS 100   // 10Hz 打印；模块内部更新 100Hz

// 寄存器
#define REG_VERSION    0x01
#define REG_ACCEL      0x04
#define REG_GYRO       0x0A
#define REG_EULER      0x26

// 缩放
#define ACCEL_SCALE    16.0f      // ±16g
#define GYRO_SCALE     2000.0f    // ±2000°/s

// ------------------------------------------------------------------
// 工具
// ------------------------------------------------------------------
bool imuRead(uint8_t reg, uint8_t *buf, uint8_t len) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((uint8_t)IMU_ADDR, (uint8_t)len, (uint8_t)true) != len) {
    return false;
  }
  for (uint8_t i = 0; i < len; i++) {
    buf[i] = (uint8_t)Wire.read();
  }
  return true;
}

float f32le(const uint8_t *b) {
  uint32_t u = (uint32_t)b[0] |
               ((uint32_t)b[1] << 8) |
               ((uint32_t)b[2] << 16) |
               ((uint32_t)b[3] << 24);
  float f;
  memcpy(&f, &u, sizeof(f));
  return f;
}

int16_t i16le(const uint8_t *b) {
  return (int16_t)((uint16_t)b[0] | ((uint16_t)b[1] << 8));
}

// ------------------------------------------------------------------
// 数据
// ------------------------------------------------------------------
float rollDeg = 0, pitchDeg = 0, yawDeg = 0;
float rollRad = 0, pitchRad = 0, yawRad = 0;
float tiltDeg = 0;
float azimuthDeg = 0;
float ax = 0, ay = 0, az = 0;       // g
float gx = 0, gy = 0, gz = 0;       // °/s
uint8_t version[3] = {0, 0, 0};
uint32_t lastPrint = 0;
uint32_t readErrors = 0;

void readVersion() {
  if (imuRead(REG_VERSION, version, 3)) {
    Serial.printf("IMU 版本: v%d.%d.%d\n", version[0], version[1], version[2]);
  } else {
    Serial.println("读版本失败：检查 I2C 地址/接线/供电");
  }
}

bool readAll() {
  uint8_t buf[12];

  // 欧拉角（弧度，float32 小端）
  if (!imuRead(REG_EULER, buf, 12)) return false;
  rollRad  = f32le(buf + 0);
  pitchRad = f32le(buf + 4);
  yawRad   = f32le(buf + 8);

  // 加速度（g）
  if (!imuRead(REG_ACCEL, buf, 6)) return false;
  ax = i16le(buf + 0) * ACCEL_SCALE / 32767.0f;
  ay = i16le(buf + 2) * ACCEL_SCALE / 32767.0f;
  az = i16le(buf + 4) * ACCEL_SCALE / 32767.0f;

  // 陀螺仪（°/s）
  if (!imuRead(REG_GYRO, buf, 6)) return false;
  gx = i16le(buf + 0) * GYRO_SCALE / 32767.0f;
  gy = i16le(buf + 2) * GYRO_SCALE / 32767.0f;
  gz = i16le(buf + 4) * GYRO_SCALE / 32767.0f;

  // 角度换算
  rollDeg  = rollRad * RAD_TO_DEG;
  pitchDeg = pitchRad * RAD_TO_DEG;
  yawDeg   = yawRad * RAD_TO_DEG;

  // 重力方向与机身 Z 轴的夹角（ZYX 欧拉角）
  // 用加速度计算倾角，避免欧拉角在 >90° 时的万向锁
  // （参考 SelfRisingRobot 作者的实测：Euler 超过 90° 会异常）
  float aNorm = sqrtf(ax * ax + ay * ay + az * az);
  if (aNorm < 0.01f) aNorm = 0.01f;
  tiltDeg = acosf(constrain(az / aNorm, -1.0f, 1.0f)) * RAD_TO_DEG;

  // 倒下方向（重力在机身 XY 平面的投影）；直立时无意义
  azimuthDeg = atan2f(ay, ax) * RAD_TO_DEG;

  return true;
}

// ------------------------------------------------------------------
// setup / loop
// ------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("Juxi 6-axis IMU I2C test (ESP32)");
  Serial.println("6-axis: no Mag/BARO; yaw drift is expected, use accelerometer azimuth.");
  Serial.printf("I2C addr=0x%02X, clock=%d Hz\n", IMU_ADDR, I2C_HZ);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(I2C_HZ);

  Serial.printf("等待模块启动 %d ms...\n", STARTUP_WAIT_MS);
  for (int i = STARTUP_WAIT_MS / 1000; i > 0; i--) {
    Serial.printf("%d...\n", i);
    delay(1000);
  }

  readVersion();
  Serial.println("输出格式: roll,pitch,yaw,tilt,azimuth,ax,ay,az,gx,gy,gz");
  Serial.println("保持静止/直立；如果数据异常，先检查地址 0x23、100kHz、共地、3.3V。");
}

void loop() {
  if (millis() - lastPrint >= PRINT_INTERVAL_MS) {
    lastPrint = millis();

    if (readAll()) {
      Serial.printf("%.2f,%.2f,%.2f,%.2f,%.1f,%.3f,%.3f,%.3f,%.1f,%.1f,%.1f\n",
                    rollDeg, pitchDeg, yawDeg, tiltDeg, azimuthDeg,
                    ax, ay, az, gx, gy, gz);
    } else {
      readErrors++;
      if (readErrors % 10 == 1) {
        Serial.printf("读取失败（累计 %lu）：检查接线/地址/供电\n",
                      (unsigned long)readErrors);
      }
    }
  }
}
