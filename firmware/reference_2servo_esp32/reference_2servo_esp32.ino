/*
 * SR-Support 两舵机参考骨架（未实机验证）
 * ------------------------------------------------------------------
 * 方案：底部舵机旋转方位 + 顶部舵机甩棍打击
 *   - IMU：Juxi 6 轴 IMU（无 Mag/BARO），I2C 0x23，100 kHz，上电等 5 s
 *   - 6 轴 yaw 会漂移，不要用 yaw 瞄准；用加速度计 atan2(ay, ax) 的 azimuth
 *   - 底部方位舵机：GPIO18（LEDC ch0）
 *   - 顶部打击舵机：GPIO19（LEDC ch1）
 *   - 两个舵机独立 5V/3A 供电，与 ESP32 共地；舵机端 2200µF
 *
 * 控制思路：
 *   1. 倾角 > AIM_TILT_DEG 或角速度 > AIM_GYRO_DPS：先让底部舵机瞄准倒地方向
 *   2. 倾角 > STRIKE_TILT_DEG 或角速度 > STRIKE_GYRO_DPS：
 *      顶部舵机向对应侧甩棍
 *   3. 保持/观察/收棍/冷却；失败重试，最多 MAX_ATTEMPTS 次
 *
 * 重要：
 *   - 这是骨架，不是成品；棍长、舵机角度、顶部 A/B 侧、方位 offset
 *     都必须按你的机械结构标定。
 *   - 顶部舵机建议 MG90S 金属齿轮；SG90 塑料齿轮在打击冲击下很容易扫齿。
 *   - 先空打（不接触地），再慢速倒地轻打，最后完整测试。
 *   - 如果底部角度方向反了：把 AZIMUTH_OFFSET_DEG 加 180，或交换
 *     BOTTOM_MIN_US / BOTTOM_MAX_US。
 *   - 顶部 A/B 侧反了：交换 TOP_A_US / TOP_B_US。
 *   - 顶部 270° 位置舵机：中位 1500≈135°，±90° 约 833/2167µs（按 datasheet），
 *     TOP_A_US/TOP_B_US 需要重算，不要直接沿用 1000/2000。
 *   - 本骨架假设：底部 180° 位置舵机 + 顶部水平轴、中位收棍、A/B 双向。
 *     如果底部是**真 360° 位置舵机**（角度可控）：把 BOTTOM_MIN_US/MAX_US 改成
 *     500/2500（按 datasheet），BOTTOM_ANGLE_RANGE_DEG 和 BOTTOM_AIM_MOD_DEG
 *     都改成 360.0f；computeAim 会自动用 az（不再 mod 180），顶部固定 A。
 *     如果底部是 **270° 位置舵机**（金属齿轮）：BOTTOM_MIN_US/MAX_US 改 500/2500
 *     （按 datasheet），BOTTOM_ANGLE_RANGE_DEG=270，BOTTOM_AIM_MOD_DEG 保持 180；
 *     顶部仍需双向 ±90°，才能覆盖 360°（有 90° 重叠）。
 *     如果底部是 360° 连续：需要 AS5600/零位开关 + 滑环/限位 + 刹车；
 *     bottomSetAngle() 不能直接用（连续舵机 PWM 是速度，不是角度）。
 *     如果顶部只能单向/竖直轴：180° 不能覆盖 360° 方位；需要底部 360° 带反馈，
 *     或顶部 270°/360°；topStrike(A/B) 也要改。
 */

#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <string.h>

#if __has_include(<esp_arduino_version.h>)
#include <esp_arduino_version.h>
#endif

// ------------------------------------------------------------------
// 引脚/IMU
// ------------------------------------------------------------------
#define SDA_PIN        21
#define SCL_PIN        22
#define IMU_ADDR       0x23
#define I2C_HZ         100000

#define BOTTOM_PIN     18
#define TOP_PIN        19
#define BOTTOM_CH      0
#define TOP_CH         1

// ------------------------------------------------------------------
// 舵机脉宽（微秒）
// 底部：0–BOTTOM_ANGLE_RANGE_DEG 对应 BOTTOM_MIN_US–BOTTOM_MAX_US
// 顶部：中位收棍；A/B 两侧分别甩出
//
// 底部是 180° 位置舵机：保持 1000/2000、180/180。
// 底部是真 360° 位置舵机（角度可控）：改成 500/2500、360/360。
// 底部是 360° 连续舵机：本骨架不适用（PWM 是速度，不是角度）。
// ------------------------------------------------------------------
#define BOTTOM_MIN_US          1000
#define BOTTOM_MAX_US          2000
#define BOTTOM_CENTER_US       1500   // 180° 舵机=90°；360° 位置舵机=180°，可改 500/1000 作 0° home
#define BOTTOM_ANGLE_RANGE_DEG 180.0f  // 底部舵机机械角度范围：180/270/360
#define BOTTOM_AIM_MOD_DEG     180.0f  // 180/270 + 双向顶部都用 180；真 360 位置用 360
// 270° 位置舵机配置（替换上面 BOTTOM_MIN_US/MAX_US/ANGLE_RANGE 三行；按 datasheet）：
//   BOTTOM_MIN_US=500, BOTTOM_MAX_US=2500, BOTTOM_ANGLE_RANGE_DEG=270.0f,
//   BOTTOM_AIM_MOD_DEG 保持 180.0f
// 真 360° 位置舵机配置：MIN/MAX 500/2500，RANGE=360，MOD=360（替换上面三行）
#define TOP_STOW_US            1500
#define TOP_A_US               1000
#define TOP_B_US               2000

// ------------------------------------------------------------------
// 控制参数（必须按机械结构调整）
// ------------------------------------------------------------------
#define AZIMUTH_OFFSET_DEG    0.0f   // 安装/舵机零位修正
#define AIM_TILT_DEG          12.0f  // 开始瞄准
#define STRIKE_TILT_DEG       35.0f  // 开始打击
#define EMERGENCY_TILT_DEG    55.0f  // 来不及瞄准也强行打击
#define AIM_GYRO_DPS          30.0f  // 角速度触发瞄准
#define STRIKE_GYRO_DPS       60.0f  // 角速度触发打击
#define GYRO_TRIGGER_MIN_TILT_DEG 5.0f  // 纯偏航旋转不触发，至少要有倾斜
#define UPRIGHT_TILT_DEG      15.0f
#define UPRIGHT_CONFIRM_MS    200

#define AIM_MS                150
#define STRIKE_MS             250
#define HOLD_MS               150
#define RETRACT_MS            250
#define COOLDOWN_MS           800
#define MAX_ATTEMPTS          3

// 可选：INA219 等电流检测，返回 true 表示过流
bool servoOvercurrent() {
  return false;
}

// ------------------------------------------------------------------
// LEDC 兼容层
// ------------------------------------------------------------------
#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
  #define SR_LEDC_NEW_API 1
#else
  #define SR_LEDC_NEW_API 0
#endif

void servoInit() {
#if SR_LEDC_NEW_API
  ledcAttach(BOTTOM_PIN, 50, 14);
  ledcAttach(TOP_PIN, 50, 14);
#else
  ledcSetup(BOTTOM_CH, 50, 14);
  ledcAttachPin(BOTTOM_PIN, BOTTOM_CH);
  ledcSetup(TOP_CH, 50, 14);
  ledcAttachPin(TOP_PIN, TOP_CH);
#endif
}

void servoPulse(uint8_t channel, uint8_t pin, uint16_t us) {
  // 允许 500–2500 µs，兼容 180°/270°/真 360° 位置舵机
  us = (uint16_t)constrain((int)us, 500, 2500);
  uint32_t duty = (uint32_t)(((uint64_t)us * 16383ULL) / 20000ULL);
#if SR_LEDC_NEW_API
  (void)channel;
  ledcWrite(pin, duty);
#else
  (void)pin;
  ledcWrite(channel, duty);
#endif
}

void bottomSetAngle(float angleDeg) {
  angleDeg = constrain(angleDeg, 0.0f, BOTTOM_ANGLE_RANGE_DEG);
  uint16_t us = (uint16_t)(BOTTOM_MIN_US +
                 (BOTTOM_MAX_US - BOTTOM_MIN_US) *
                 (angleDeg / BOTTOM_ANGLE_RANGE_DEG));
  servoPulse(BOTTOM_CH, BOTTOM_PIN, us);
}

void bottomCenter() {
  servoPulse(BOTTOM_CH, BOTTOM_PIN, BOTTOM_CENTER_US);
}

void topStow() {
  servoPulse(TOP_CH, TOP_PIN, TOP_STOW_US);
}

void topStrike(int side) {
  servoPulse(TOP_CH, TOP_PIN, side >= 0 ? TOP_A_US : TOP_B_US);
}

// ------------------------------------------------------------------
// IMU
// ------------------------------------------------------------------
bool imuRead(uint8_t reg, uint8_t *buf, uint8_t len) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((uint8_t)IMU_ADDR, (uint8_t)len, (uint8_t)true) != len) {
    return false;
  }
  for (uint8_t i = 0; i < len; i++) buf[i] = (uint8_t)Wire.read();
  return true;
}

float f32le(const uint8_t *b) {
  uint32_t u = (uint32_t)b[0] | ((uint32_t)b[1] << 8) |
               ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
  float f;
  memcpy(&f, &u, sizeof(f));
  return f;
}

int16_t i16le(const uint8_t *b) {
  return (int16_t)((uint16_t)b[0] | ((uint16_t)b[1] << 8));
}

float rollDeg = 0, pitchDeg = 0, yawDeg = 0;
float rollRad = 0, pitchRad = 0, yawRad = 0;
float tiltDeg = 0;
float azimuthDeg = 0;
float ax = 0, ay = 0, az = 0;   // g
float gx = 0, gy = 0, gz = 0;   // °/s
float gyroNorm = 0;
uint8_t imuVersion[3] = {0, 0, 0};

bool readImuAll() {
  uint8_t buf[12];

  if (!imuRead(0x26, buf, 12)) return false;  // Euler
  rollRad  = f32le(buf + 0);
  pitchRad = f32le(buf + 4);
  yawRad   = f32le(buf + 8);

  if (!imuRead(0x04, buf, 6)) return false;   // Accel
  ax = i16le(buf + 0) * 16.0f / 32767.0f;
  ay = i16le(buf + 2) * 16.0f / 32767.0f;
  az = i16le(buf + 4) * 16.0f / 32767.0f;

  if (!imuRead(0x0A, buf, 6)) return false;   // Gyro
  gx = i16le(buf + 0) * 2000.0f / 32767.0f;
  gy = i16le(buf + 2) * 2000.0f / 32767.0f;
  gz = i16le(buf + 4) * 2000.0f / 32767.0f;

  rollDeg  = rollRad * RAD_TO_DEG;
  pitchDeg = pitchRad * RAD_TO_DEG;
  yawDeg   = yawRad * RAD_TO_DEG;

  // 重力方向与机身 Z 轴的夹角（ZYX Euler）
  // 用加速度计算倾角，避免欧拉角在 >90° 时的万向锁
  // （参考 SelfRisingRobot 作者的实测：Euler 超过 90° 会异常）
  float aNorm = sqrtf(ax * ax + ay * ay + az * az);
  if (aNorm < 0.01f) aNorm = 0.01f;
  tiltDeg = acosf(constrain(az / aNorm, -1.0f, 1.0f)) * RAD_TO_DEG;

  // 倒下方向：重力在机身 XY 平面的投影
  azimuthDeg = atan2f(ay, ax) * RAD_TO_DEG;

  gyroNorm = sqrtf(gx * gx + gy * gy + gz * gz);
  return true;
}

void readVersion() {
  if (imuRead(0x01, imuVersion, 3)) {
    Serial.printf("IMU 版本: v%d.%d.%d\n", imuVersion[0], imuVersion[1], imuVersion[2]);
  } else {
    Serial.println("读 IMU 版本失败：检查 0x23、100kHz、3.3V、共地");
  }
}

// ------------------------------------------------------------------
// 状态机
// ------------------------------------------------------------------
enum State {
  ST_IDLE,
  ST_AIM,
  ST_STRIKE,
  ST_HOLD,
  ST_RETRACT,
  ST_COOLDOWN
};

State state = ST_IDLE;
uint32_t stateStart = 0;
uint32_t uprightStart = 0;
bool uprightTimerActive = false;
bool autoMode = true;
bool retryLockout = false;
bool verbose = true;
int attempts = 0;
int topSide = +1;
float bottomAngle = 90.0f;
uint32_t lastLoop = 0;
uint32_t lastCsv = 0;
uint32_t readErrors = 0;

const char* stateName(State s) {
  switch (s) {
    case ST_IDLE:     return "IDLE";
    case ST_AIM:      return "AIM";
    case ST_STRIKE:   return "STRIKE";
    case ST_HOLD:     return "HOLD";
    case ST_RETRACT:  return "RETRACT";
    case ST_COOLDOWN: return "COOLDOWN";
    default:          return "?";
  }
}

void computeAim() {
  float az = fmodf(azimuthDeg + AZIMUTH_OFFSET_DEG + 360.0f, 360.0f);
  // 180° 底部：一个平面覆盖两个相反方向，用 mod 180 + A/B 两侧
  // 360° 位置底部：直接指到 az，顶部固定 A
  bottomAngle = fmodf(az, BOTTOM_AIM_MOD_DEG);
  if (BOTTOM_AIM_MOD_DEG >= 359.9f) {
    topSide = +1;
  } else {
    topSide = (az < 180.0f) ? +1 : -1;
  }
}

void enterState(State s) {
  state = s;
  stateStart = millis();

  switch (s) {
    case ST_IDLE:
      topStow();
      bottomCenter();
      Serial.println("状态: IDLE（收棍/回中）");
      break;

    case ST_AIM:
      computeAim();
      bottomSetAngle(bottomAngle);
      Serial.printf("状态: AIM（方位 %.1f°，底部 %.1f°，顶部侧 %s）\n",
                    azimuthDeg, bottomAngle, topSide > 0 ? "A" : "B");
      break;

    case ST_STRIKE:
      attempts++;
      topStrike(topSide);
      Serial.printf("状态: STRIKE（第 %d/%d 次，顶部 %s）\n",
                    attempts, MAX_ATTEMPTS, topSide > 0 ? "A" : "B");
      break;

    case ST_HOLD:
      Serial.println("状态: HOLD");
      break;

    case ST_RETRACT:
      topStow();
      Serial.println("状态: RETRACT（收棍）");
      break;

    case ST_COOLDOWN:
      topStow();
      Serial.println("状态: COOLDOWN");
      break;
  }
}

bool uprightStableNow(uint32_t now) {
  bool upright = tiltDeg < UPRIGHT_TILT_DEG;
  if (upright) {
    if (!uprightTimerActive) {
      uprightTimerActive = true;
      uprightStart = now;
    }
  } else {
    uprightTimerActive = false;
  }
  return uprightTimerActive && (now - uprightStart >= UPRIGHT_CONFIRM_MS);
}

void updateStateMachine() {
  uint32_t now = millis();
  bool uprightStable = uprightStableNow(now);

  switch (state) {
    case ST_IDLE:
      if (retryLockout) {
        if (uprightStable) {
          retryLockout = false;
          attempts = 0;
          Serial.println("已恢复直立，解除锁定");
        }
        break;
      }
      if (tiltDeg > AIM_TILT_DEG ||
          (tiltDeg > GYRO_TRIGGER_MIN_TILT_DEG && gyroNorm > AIM_GYRO_DPS)) {
        enterState(ST_AIM);
      }
      break;

    case ST_AIM:
      if (tiltDeg < AIM_TILT_DEG && gyroNorm < AIM_GYRO_DPS) {
        enterState(ST_IDLE);  // 已经回正，取消
      } else if (now - stateStart >= AIM_MS) {
        bool strike = (tiltDeg > STRIKE_TILT_DEG) ||
                      (tiltDeg > GYRO_TRIGGER_MIN_TILT_DEG && gyroNorm > STRIKE_GYRO_DPS) ||
                      (tiltDeg > EMERGENCY_TILT_DEG) ||
                      (now - stateStart >= AIM_MS + 100 && tiltDeg > AIM_TILT_DEG);
        if (strike) enterState(ST_STRIKE);
      }
      break;

    case ST_STRIKE:
      if (servoOvercurrent()) {
        Serial.println("过流：收棍");
        enterState(ST_RETRACT);
      } else if (now - stateStart >= STRIKE_MS) {
        enterState(ST_HOLD);
      }
      break;

    case ST_HOLD:
      if (now - stateStart >= HOLD_MS) {
        enterState(ST_RETRACT);
      }
      break;

    case ST_RETRACT:
      if (now - stateStart >= RETRACT_MS) {
        enterState(ST_COOLDOWN);
      }
      break;

    case ST_COOLDOWN:
      if (now - stateStart >= COOLDOWN_MS) {
        if (uprightStable) {
          attempts = 0;
          enterState(ST_IDLE);
        } else if (servoOvercurrent()) {
          Serial.println("过流：锁定");
          retryLockout = true;
          enterState(ST_IDLE);
        } else if (attempts < MAX_ATTEMPTS) {
          enterState(ST_AIM);
        } else {
          Serial.println("多次失败，锁定；直立或按 a 解除");
          retryLockout = true;
          enterState(ST_IDLE);
        }
      }
      break;
  }
}

// ------------------------------------------------------------------
// 串口命令
// ------------------------------------------------------------------
void printHelp() {
  Serial.println("命令: a=自动/手动 c=收棍回中 b=按当前方位瞄准 s=顶部A S=顶部B r=收棍回中 p=角度 v=详细 ?=帮助");
}

void printAngles() {
  Serial.printf("tilt=%.1f az=%.1f bottom=%.1f side=%s gyro=%.1f state=%s attempts=%d\n",
                tiltDeg, azimuthDeg, bottomAngle,
                topSide > 0 ? "A" : "B", gyroNorm, stateName(state), attempts);
}

void handleCommand(char c) {
  switch (c) {
    case 'a':
      autoMode = !autoMode;
      attempts = 0;
      retryLockout = false;
      uprightTimerActive = false;
      enterState(ST_IDLE);
      Serial.printf("自动模式: %s\n", autoMode ? "开" : "关");
      break;
    case 'c':
      autoMode = false;
      enterState(ST_IDLE);
      break;
    case 'b':
      autoMode = false;
      computeAim();
      bottomSetAngle(bottomAngle);
      Serial.printf("手动瞄准: az=%.1f bottom=%.1f side=%s\n",
                    azimuthDeg, bottomAngle, topSide > 0 ? "A" : "B");
      break;
    case 's':
      autoMode = false;
      topStrike(+1);
      Serial.println("手动顶部 A");
      break;
    case 'S':
      autoMode = false;
      topStrike(-1);
      Serial.println("手动顶部 B");
      break;
    case 'r':
      autoMode = false;
      topStow();
      bottomCenter();
      Serial.println("手动收棍/回中");
      break;
    case 'p':
      printAngles();
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
  Serial.println("SR-Support 2-servo reference skeleton");
  Serial.println("bottom azimuth + top strike; Juxi 6-axis IMU 0x23 (no Mag/BARO)");
  printHelp();

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(I2C_HZ);

  servoInit();
  topStow();
  bottomCenter();

  Serial.println("等待 IMU 启动 5 s（保持设备静止/直立）...");
  for (int i = 5; i > 0; i--) {
    Serial.printf("%d...\n", i);
    delay(1000);
  }

  readVersion();
  if (!readImuAll()) {
    Serial.println("IMU 读取失败：检查 0x23、100kHz、3.3V、共地");
    while (true) delay(1000);
  }

  Serial.println("就绪。先空打测试，再慢速倒地测试。");
  enterState(ST_IDLE);
}

void loop() {
  handleSerial();

  if (millis() - lastLoop >= 10) {  // 100Hz
    lastLoop = millis();

    if (readImuAll()) {
      if (autoMode) updateStateMachine();
    } else {
      readErrors++;
      // 安全：IMU 失效时收棍/回中，避免舵机一直保持在打击位
      if (readErrors == 1 || state != ST_IDLE) {
        Serial.println("IMU 读取失败：收棍/回中");
        enterState(ST_IDLE);
      }
      if (readErrors % 50 == 1) {
        Serial.printf("IMU 读取失败（累计 %lu）\n", (unsigned long)readErrors);
      }
    }

    if (verbose && millis() - lastCsv >= 100) {
      lastCsv = millis();
      Serial.printf("%.1f,%.1f,%.1f,%.1f,%.1f,%d,%.1f\n",
                    rollDeg, pitchDeg, tiltDeg, azimuthDeg,
                    bottomAngle, topSide, gyroNorm);
    }
  }
}
