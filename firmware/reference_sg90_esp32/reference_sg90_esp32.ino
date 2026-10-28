/*
 * SR-Support 参考固件（未实机验证）
 * ------------------------------------------------------------------
 * 硬件：
 *   - ESP32 DevKit V1 / NodeMCU-32S（C3 SuperMini 需改引脚）
 *   - MPU6050（GY-521，6 轴，I2C）
 *   - SG90 180° 位置舵机（1 个）
 *   - 舵机独立 5V/2A 供电，与 ESP32 共地；舵机端 1000µF + 100nF
 *
 * 功能：
 *   - 读取 MPU6050 原始数据（不依赖第三方 IMU 库）
 *   - 开机陀螺零偏校准
 *   - 互补滤波计算 roll / pitch / tilt
 *   - 倾角 > 50° 持续 200ms 且角速度较低 -> 展臂
 *   - 展臂 -> 保持 -> 收臂 -> 冷却 -> 重试（最多 3 次）
 *   - 串口命令：c 校准 / a 自动模式 / d 前展 / b 后展 / r 收臂
 *                p 打印角度 / s 状态 / v 详细输出 / ? 帮助
 *
 * 重要：
 *   - 这是参考实现，不是经过硬件验证的成品。
 *   - 首次测试先不接舵机，确认串口角度；再空载测舵机；最后装臂。
 *   - 如果前/后方向相反，交换 SERVO_FWD_US / SERVO_BACK_US，
 *     或把 PITCH_SIGN 改成 -1.0f。
 *   - SG90 塑料齿轮怕堵转：保持时间不要超过 0.5s，建议加舵机保护器。
 */

#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#if __has_include(<esp_arduino_version.h>)
#include <esp_arduino_version.h>
#endif

// ------------------------------------------------------------------
// 引脚配置（ESP32 DevKit V1 默认）
// C3 SuperMini 示例：SDA=4, SCL=5, SERVO=3；请按实际板子修改。
// ------------------------------------------------------------------
#define SDA_PIN       21
#define SCL_PIN       22
#define SERVO_PIN     18

// ------------------------------------------------------------------
// 舵机脉宽（单位：微秒）
// 1500 = 中位（摆臂竖直收在机身外侧/槽内；按实际装配标定）
// 1000 / 2000 = 两个展开方向（不一定是水平，必须按实际 CAD/装配标定）
// 先空载确认机械不顶死，再装臂。
// ------------------------------------------------------------------
#define SERVO_MIN_US   1000
#define SERVO_MAX_US   2000
#define SERVO_STOW_US  1500
#define SERVO_FWD_US   1000
#define SERVO_BACK_US  2000

// LEDC：50Hz，16 位
#define SERVO_FREQ_HZ  50
#define SERVO_RES_BITS 14
#define SERVO_CHANNEL  0

// ------------------------------------------------------------------
// MPU6050
// ------------------------------------------------------------------
#define MPU_ADDR       0x68
#define MPU_REG_SMPLRT_DIV   0x19
#define MPU_REG_CONFIG       0x1A
#define MPU_REG_GYRO_CONFIG  0x1B
#define MPU_REG_ACCEL_CONFIG 0x1C
#define MPU_REG_ACCEL_XOUT_H 0x3B
#define MPU_REG_PWR_MGMT_1   0x6B
#define MPU_REG_WHO_AM_I     0x75

// 量程：陀螺 ±500°/s -> 65.5 LSB/(°/s)
//      加速度 ±4g     -> 8192 LSB/g
#define GYRO_LSB_PER_DPS  65.5f
#define ACCEL_LSB_PER_G   8192.0f

// ------------------------------------------------------------------
// 控制参数（按你的机械结构调整）
// ------------------------------------------------------------------
#define FALL_TILT_DEG       50.0f   // 倒地判定角
#define UPRIGHT_TILT_DEG    15.0f   // 直立判定角（滞回）
#define FALL_CONFIRM_MS     200     // 倒地确认时间
#define UPRIGHT_CONFIRM_MS  300     // 直立确认时间
#define GYRO_QUIET_DPS      60.0f   // 认为“已停稳”的角速度阈值
#define DEPLOY_MS           600     // 展臂时间
#define HOLD_MS             400     // 撑地保持时间（SG90 建议 <=500ms）
#define RETRACT_MS          500     // 收臂时间
#define COOLDOWN_MS         1000    // 冷却/重试间隔
#define MAX_ATTEMPTS        3       // 最多尝试次数

// 如果安装方向相反，把对应 SIGN 改成 -1.0f
#define PITCH_SIGN  1.0f
#define ROLL_SIGN   1.0f

// 互补滤波系数（100Hz 下 0.98 约 0.5s 时间常数）
#define COMP_ALPHA  0.98f

// ------------------------------------------------------------------
// 全局状态
// ------------------------------------------------------------------
struct ImuData {
  float ax, ay, az;  // g
  float gx, gy, gz;  // °/s（已减零偏）
};

ImuData imu;
float gyroBiasX = 0.0f;
float gyroBiasY = 0.0f;
float gyroBiasZ = 0.0f;

float roll = 0.0f;
float pitch = 0.0f;
float tilt = 0.0f;
float accelNorm = 1.0f;

uint32_t lastImuMicros = 0;
uint32_t lastGoodImuMillis = 0;
uint32_t lastPrintMillis = 0;
bool verbose = true;

enum State {
  ST_IDLE,
  ST_DEPLOY,
  ST_HOLD,
  ST_RETRACT,
  ST_COOLDOWN
};

State state = ST_IDLE;
uint32_t stateStartMillis = 0;
uint32_t fallStartMillis = 0;
bool fallTimerActive = false;
uint32_t uprightStartMillis = 0;
bool uprightTimerActive = false;
int attempts = 0;
int deployDir = +1;  // +1 前，-1 后
bool autoMode = true;
bool retryLockout = false;  // 多次失败后锁定，直立或按 a 解除

// ------------------------------------------------------------------
// LEDC 兼容层：Arduino-ESP32 2.x / 3.x
// ------------------------------------------------------------------
#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  #define SR_LEDC_NEW_API 1
#else
  #define SR_LEDC_NEW_API 0
#endif

void servoInit() {
#if SR_LEDC_NEW_API
  ledcAttach(SERVO_PIN, SERVO_FREQ_HZ, SERVO_RES_BITS);
#else
  ledcSetup(SERVO_CHANNEL, SERVO_FREQ_HZ, SERVO_RES_BITS);
  ledcAttachPin(SERVO_PIN, SERVO_CHANNEL);
#endif
}

void servoPulse(uint16_t pulseUs) {
  pulseUs = (uint16_t)constrain((int)pulseUs, SERVO_MIN_US, SERVO_MAX_US);
  // duty = pulseUs / 20000us * 16383
  uint32_t duty = (uint32_t)(((uint64_t)pulseUs * 16383ULL) / 20000ULL);
#if SR_LEDC_NEW_API
  ledcWrite(SERVO_PIN, duty);
#else
  ledcWrite(SERVO_CHANNEL, duty);
#endif
}

// ------------------------------------------------------------------
// MPU6050 底层
// ------------------------------------------------------------------
void mpuWrite(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

uint8_t mpuRead(uint8_t reg) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)1, (uint8_t)true);
  if (Wire.available() < 1) return 0xFF;
  return Wire.read();
}

bool mpuInit() {
  mpuWrite(MPU_REG_PWR_MGMT_1, 0x00);  // 唤醒
  delay(50);
  mpuWrite(MPU_REG_PWR_MGMT_1, 0x01);  // PLL with X gyro
  mpuWrite(MPU_REG_SMPLRT_DIV, 0x09);  // 1kHz / (1+9) = 100Hz
  mpuWrite(MPU_REG_CONFIG, 0x03);       // DLPF 44Hz
  mpuWrite(MPU_REG_GYRO_CONFIG, 0x08);  // ±500°/s
  mpuWrite(MPU_REG_ACCEL_CONFIG, 0x08); // ±4g
  delay(50);

  uint8_t who = mpuRead(MPU_REG_WHO_AM_I);
  Serial.printf("IMU WHO_AM_I = 0x%02X (MPU6050 期望 0x68；MPU6500 常见 0x70)\n", who);
  // MPU6050: 0x68；MPU6500/9250 等常见 0x70/0x71/0x73/0x98
  return (who == 0x68 || who == 0x70 || who == 0x71 ||
          who == 0x73 || who == 0x98);
}

bool readImu(ImuData &out) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(MPU_REG_ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)14, (uint8_t)true);
  if (Wire.available() < 14) return false;

  int16_t rawAx = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t rawAy = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t rawAz = (int16_t)((Wire.read() << 8) | Wire.read());
  (void)Wire.read();  // 温度高字节
  (void)Wire.read();  // 温度低字节
  int16_t rawGx = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t rawGy = (int16_t)((Wire.read() << 8) | Wire.read());
  int16_t rawGz = (int16_t)((Wire.read() << 8) | Wire.read());

  out.ax = rawAx / ACCEL_LSB_PER_G;
  out.ay = rawAy / ACCEL_LSB_PER_G;
  out.az = rawAz / ACCEL_LSB_PER_G;
  out.gx = rawGx / GYRO_LSB_PER_DPS - gyroBiasX;
  out.gy = rawGy / GYRO_LSB_PER_DPS - gyroBiasY;
  out.gz = rawGz / GYRO_LSB_PER_DPS - gyroBiasZ;
  return true;
}

// ------------------------------------------------------------------
// 陀螺零偏校准：开机保持静止约 1 秒
// ------------------------------------------------------------------
void calibrateGyro() {
  const int N = 500;
  double sx = 0, sy = 0, sz = 0;
  int n = 0;

  Serial.println("校准陀螺零偏：请保持设备静止...");
  delay(300);

  for (int i = 0; i < N; i++) {
    ImuData d;
    if (readImu(d)) {
      // readImu 已减去旧零偏；这里先加回去，避免重复校准叠加
      sx += d.gx + gyroBiasX;
      sy += d.gy + gyroBiasY;
      sz += d.gz + gyroBiasZ;
      n++;
    }
    delay(2);
  }

  if (n > 0) {
    gyroBiasX = (float)(sx / n);
    gyroBiasY = (float)(sy / n);
    gyroBiasZ = (float)(sz / n);
  }

  roll = 0.0f;
  pitch = 0.0f;
  tilt = 0.0f;
  Serial.printf("零偏: gx=%.2f gy=%.2f gz=%.2f °/s (n=%d)\n",
                gyroBiasX, gyroBiasY, gyroBiasZ, n);
}

// ------------------------------------------------------------------
// 姿态更新：互补滤波
// ------------------------------------------------------------------
void updateAngles(const ImuData &d, float dt) {
  float rollAcc = atan2f(d.ay, d.az) * RAD_TO_DEG;
  float pitchAcc = atan2f(-d.ax, sqrtf(d.ay * d.ay + d.az * d.az)) * RAD_TO_DEG;

  roll  = COMP_ALPHA * (roll  + ROLL_SIGN  * d.gx * dt) +
          (1.0f - COMP_ALPHA) * (ROLL_SIGN  * rollAcc);
  pitch = COMP_ALPHA * (pitch + PITCH_SIGN * d.gy * dt) +
          (1.0f - COMP_ALPHA) * (PITCH_SIGN * pitchAcc);

  accelNorm = sqrtf(d.ax * d.ax + d.ay * d.ay + d.az * d.az);
  if (accelNorm < 0.01f) accelNorm = 0.01f;

  // 重力方向与机身 z 轴的夹角
  tilt = acosf(constrain(d.az / accelNorm, -1.0f, 1.0f)) * RAD_TO_DEG;
}

// ------------------------------------------------------------------
// 状态机
// ------------------------------------------------------------------
const char* stateName(State s) {
  switch (s) {
    case ST_IDLE:     return "IDLE";
    case ST_DEPLOY:   return "DEPLOY";
    case ST_HOLD:     return "HOLD";
    case ST_RETRACT:  return "RETRACT";
    case ST_COOLDOWN: return "COOLDOWN";
    default:          return "?";
  }
}

void goState(State s) {
  state = s;
  stateStartMillis = millis();

  switch (s) {
    case ST_IDLE:
      fallTimerActive = false;
      break;
    case ST_DEPLOY:
      servoPulse(deployDir > 0 ? SERVO_FWD_US : SERVO_BACK_US);
      Serial.printf("展臂: %s\n", deployDir > 0 ? "前" : "后");
      break;
    case ST_RETRACT:
      servoPulse(SERVO_STOW_US);
      Serial.println("收臂");
      break;
    default:
      break;
  }
}

// 可选：接入 INA219 后在这里返回 true
bool servoOvercurrent() {
  return false;
}

bool isFallenNow() {
  bool quiet = fabsf(imu.gx) < GYRO_QUIET_DPS &&
               fabsf(imu.gy) < GYRO_QUIET_DPS;
  bool normalG = accelNorm > 0.8f && accelNorm < 1.2f;
  return (tilt > FALL_TILT_DEG) && quiet && normalG;
}

bool isUprightNow() {
  return tilt < UPRIGHT_TILT_DEG;
}

void updateStateMachine() {
  uint32_t now = millis();
  bool fallen = isFallenNow();
  bool upright = isUprightNow();

  // 直立去抖：必须连续直立 UPRIGHT_CONFIRM_MS 才认为稳定
  if (upright) {
    if (!uprightTimerActive) {
      uprightTimerActive = true;
      uprightStartMillis = now;
    }
  } else {
    uprightTimerActive = false;
  }
  bool uprightStable = uprightTimerActive &&
                       (now - uprightStartMillis >= UPRIGHT_CONFIRM_MS);

  // 侧倒检测：横滚明显大于俯仰 -> 单轴臂救不了
  bool sideFall = fabsf(roll) > fabsf(pitch) + 20.0f;

  switch (state) {
    case ST_IDLE:
      if (retryLockout) {
        if (uprightStable) {
          retryLockout = false;
          attempts = 0;
          Serial.println("已恢复直立，解除重试锁定");
        }
        break;
      }
      if (fallen) {
        if (!fallTimerActive) {
          fallTimerActive = true;
          fallStartMillis = now;
        } else if (now - fallStartMillis >= FALL_CONFIRM_MS) {
          if (sideFall) {
            static uint32_t lastWarn = 0;
            if (now - lastWarn > 1000) {
              lastWarn = now;
              Serial.println("检测到侧倒：单轴摆臂无法扶正（需第二舵机/被动底座）");
            }
            fallTimerActive = false;
          } else {
            deployDir = (pitch >= 0.0f) ? +1 : -1;
            attempts = 1;
            goState(ST_DEPLOY);
          }
        }
      } else {
        fallTimerActive = false;
      }
      break;

    case ST_DEPLOY:
      if (servoOvercurrent()) {
        Serial.println("过流保护：收臂");
        goState(ST_RETRACT);
      } else if (now - stateStartMillis >= DEPLOY_MS) {
        goState(ST_HOLD);
      }
      break;

    case ST_HOLD:
      if (servoOvercurrent()) {
        Serial.println("过流保护：收臂");
        goState(ST_RETRACT);
      } else if (uprightStable) {
        goState(ST_RETRACT);
      } else if (now - stateStartMillis >= HOLD_MS) {
        goState(ST_RETRACT);
      }
      break;

    case ST_RETRACT:
      if (now - stateStartMillis >= RETRACT_MS) {
        goState(ST_COOLDOWN);
      }
      break;

    case ST_COOLDOWN:
      if (now - stateStartMillis >= COOLDOWN_MS) {
        if (uprightStable) {
          attempts = 0;
          goState(ST_IDLE);
        } else if (sideFall) {
          Serial.println("侧倒不在单轴能力范围内，停止重试");
          attempts = 0;
          goState(ST_IDLE);
        } else if (attempts < MAX_ATTEMPTS) {
          attempts++;
          Serial.printf("重试 %d/%d\n", attempts, MAX_ATTEMPTS);
          goState(ST_DEPLOY);
        } else {
          Serial.println("多次尝试失败，锁定；直立或按 a 解除");
          attempts = 0;
          retryLockout = true;
          goState(ST_IDLE);
        }
      }
      break;
  }
}

// ------------------------------------------------------------------
// 串口命令
// ------------------------------------------------------------------
void printHelp() {
  Serial.println("命令: c=校准 a=自动/手动 d=前展 b=后展 r=收臂 p=角度 s=状态 v=详细 ?=帮助");
}

void printAngles() {
  Serial.printf("tilt=%.1f pitch=%.1f roll=%.1f gx=%.1f gy=%.1f norm=%.2f state=%s\n",
                tilt, pitch, roll, imu.gx, imu.gy, accelNorm, stateName(state));
}

void handleCommand(char c) {
  switch (c) {
    case 'c':
      autoMode = false;
      servoPulse(SERVO_STOW_US);
      delay(300);
      calibrateGyro();
      break;
    case 'a':
      autoMode = !autoMode;
      attempts = 0;
      fallTimerActive = false;
      retryLockout = false;
      servoPulse(SERVO_STOW_US);
      goState(ST_IDLE);
      Serial.printf("自动模式: %s\n", autoMode ? "开" : "关");
      break;
    case 'd':
      autoMode = false;
      servoPulse(SERVO_FWD_US);
      Serial.println("手动前展");
      break;
    case 'b':
      autoMode = false;
      servoPulse(SERVO_BACK_US);
      Serial.println("手动后展");
      break;
    case 'r':
      autoMode = false;
      servoPulse(SERVO_STOW_US);
      Serial.println("手动收臂");
      break;
    case 'p':
      printAngles();
      break;
    case 's':
      Serial.printf("状态: %s (attempts=%d, auto=%d)\n",
                    stateName(state), attempts, autoMode ? 1 : 0);
      break;
    case 'v':
      verbose = !verbose;
      Serial.printf("详细输出: %s\n", verbose ? "开" : "关");
      break;
    case '?':
      printHelp();
      break;
    default:
      break;
  }
}

void handleSerial() {
  while (Serial.available() > 0) {
    int c = Serial.read();
    if (c > 0) handleCommand((char)c);
  }
}

// ------------------------------------------------------------------
// setup / loop
// ------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("SR-Support reference firmware");
  Serial.println("ESP32 + MPU6050 + SG90 (single-axis self-righting)");
  printHelp();

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  if (!mpuInit()) {
    Serial.println("MPU6050 初始化失败：检查接线/地址/供电");
    while (true) delay(1000);
  }

  servoInit();
  servoPulse(SERVO_STOW_US);  // 先收臂
  delay(500);

  calibrateGyro();

  lastImuMicros = micros();
  lastPrintMillis = millis();
  goState(ST_IDLE);
  Serial.println("就绪：自动模式开启。先手推测试，注意舵机电源共地。");
}

void loop() {
  handleSerial();

  uint32_t nowUs = micros();
  if ((uint32_t)(nowUs - lastImuMicros) >= 10000) {  // 100Hz
    float dt = (nowUs - lastImuMicros) / 1000000.0f;
    lastImuMicros = nowUs;

    if (readImu(imu)) {
      lastGoodImuMillis = millis();
      updateAngles(imu, dt);
      if (autoMode) updateStateMachine();

      uint32_t nowMs = millis();
      if (verbose && nowMs - lastPrintMillis >= 200) {
        lastPrintMillis = nowMs;
        Serial.printf("%.1f,%.1f,%.1f\n", tilt, pitch, roll);  // Serial Plotter
      }
    }
  }

  // 安全：IMU 连续 500ms 无有效数据时收臂，避免舵机一直保持在展臂位
  if ((state == ST_DEPLOY || state == ST_HOLD) &&
      (millis() - lastGoodImuMillis > 500)) {
    Serial.println("IMU 数据超时：收臂");
    goState(ST_RETRACT);
  }
}
