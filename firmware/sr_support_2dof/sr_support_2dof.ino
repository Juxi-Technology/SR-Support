/*
 * SR-Support 2-DOF 慢速起立固件（骨架，未实机验证）
 * ------------------------------------------------------------------
 * 硬件：
 *   - ESP32-S3（示例引脚见 config.h）
 *   - Juxi 6 轴 IMU（I2C 0x23，100kHz，3.3V，上电等 5s）
 *   - 8 路舵机转接板（LEDC 直连或 PCA9685，见 SERVO_DRIVER_MODE）
 *   - v0 只用 2× PTK 7452MG 180° PWM 舵机（CH1=肩，CH2=肘）
 *   - 插电：ESP32 USB-C 5V；舵机独立 5V/3A（或 6V/3A），共地
 *
 * 功能：
 *   - IMU 读取 / 姿态解算（tilt/azimuth 用加速度计）
 *   - 倒地判定（4 种姿态）
 *   - 慢速 waypoint 起立状态机（或可选 RL 策略）
 *   - 8 路手动测试 / 串口调参 / 急停 / 重试
 *
 * 重要：
 *   - 这是骨架，不是成品；getup_sequence.h 里的 waypoint 目前是占位 {0,0}，
 *     GETUP_SEQ_READY=0 时固件拒绝自动起立，先手动整定。
 *   - 本项目为独立实现，未复制 SelfRisingRobot 代码/STL/权重；
 *     见 docs/licensing.md 与 docs/provenance.md。
 *   - 第一次测试先不接舵机/空载，确认 IMU 和串口；再装臂。
 */

#include "config.h"
#include "state.h"
#include "juxi_imu.h"
#include "servo_pair.h"
#include "getup_sequence.h"
#include "policy_runner.h"

JuxiImu imu;
ServoArm servos;

#if USE_RL_POLICY
PolicyRunner policyRunner;
#endif

State state = ST_BOOT;
uint32_t stateStart = 0;
uint32_t lastControl = 0;
uint32_t lastPrint = 0;
uint32_t lastImuGood = 0;
uint32_t fallStart = 0;
uint32_t uprightStart = 0;
uint32_t getupStart = 0;
uint32_t abortStart = 0;
uint32_t lastButtonMs = 0;
bool autoMode = true;
bool verbose = true;
bool buttonPrev = false;
bool imuReady = false;
uint8_t attempts = 0;
uint8_t selectedChannel = 0;
FallPose pose = POSE_UNKNOWN;

// ------------------------------------------------------------------
// 工具
// ------------------------------------------------------------------
const char *stateName(State s) {
  switch (s) {
    case ST_BOOT:            return "BOOT";
    case ST_SELFTEST:        return "SELFTEST";
    case ST_IDLE:            return "IDLE";
    case ST_MANUAL:          return "MANUAL";
    case ST_FALLEN_CONFIRM:  return "FALLEN_CONFIRM";
    case ST_GETUP:           return "GETUP";
    case ST_HOLD:            return "HOLD";
    case ST_DONE:            return "DONE";
    case ST_ABORT:           return "ABORT";
    case ST_FAULT:           return "FAULT";
    default:                 return "?";
  }
}

const char *poseName(FallPose p) {
  switch (p) {
    case POSE_FRONT: return "FRONT";
    case POSE_BACK:  return "BACK";
    case POSE_LEFT:  return "LEFT";
    case POSE_RIGHT: return "RIGHT";
    default:         return "UNKNOWN";
  }
}

const char *servoRoleName(uint8_t ch) {
  if (ch >= SERVO_COUNT) return "?";
  if (SERVO_ROLES[ch] == SERVO_ROLE_SHOULDER) return "SHOULDER";
  if (SERVO_ROLES[ch] == SERVO_ROLE_ELBOW) return "ELBOW";
  return "AUX";
}

void enterState(State s) {
  state = s;
  stateStart = millis();

  switch (s) {
    case ST_IDLE:
      servos.setTargetsRad(0.0f, 0.0f);
      break;
    case ST_MANUAL:
      servos.setTargetsRad(0.0f, 0.0f);
      break;
    case ST_FALLEN_CONFIRM:
      fallStart = millis();
      break;
    case ST_GETUP:
      getupStart = millis();
      uprightStart = 0;
      break;
    case ST_ABORT:
      abortStart = millis();
      servos.setTargetsRad(0.0f, 0.0f);
      break;
    case ST_FAULT:
      servos.stop();
      break;
    default:
      break;
  }

  Serial.printf("STATE -> %s\n", stateName(s));
}

// ------------------------------------------------------------------
// 起立
// ------------------------------------------------------------------
bool startGetup() {
#if !USE_RL_POLICY && !GETUP_SEQ_READY
  Serial.println("waypoint 未整定：getup_sequence.h 的 GETUP_SEQ_READY=0；"
                 "先用 m 手动整定并填入角度。");
  return false;
#else
  const JuxiImuData &d = imu.data();
  // 用加速度计推导的 roll/pitch 分类，避免 Euler >90° 万向锁
  pose = classifyFallPose(d.rollAccRad, d.pitchAccRad);
  attempts++;
  Serial.printf("GETUP start: pose=%s attempt=%u\n", poseName(pose), (unsigned)attempts);

#if USE_RL_POLICY
  policyRunner.reset(servos);
#endif

  enterState(ST_GETUP);
  return true;
#endif
}

void updateGetupTargets() {
  uint8_t p = (uint8_t)pose;
  if (p > 3) p = 0;
  uint8_t len = GETUP_SEQ_LEN[p];
  if (len == 0) len = 1;

  uint32_t elapsed = millis() - getupStart;
  uint16_t seg = elapsed / WAYPOINT_INTERP_MS;
  if (seg >= len) seg = len - 1;

  float t = (elapsed - (uint32_t)seg * WAYPOINT_INTERP_MS) /
            (float)WAYPOINT_INTERP_MS;
  if (t < 0.0f) t = 0.0f;
  if (t > 1.0f) t = 1.0f;

  Waypoint a = {0.0f, 0.0f};
  if (seg > 0) a = GETUP_SEQ[p][seg - 1];
  Waypoint b = GETUP_SEQ[p][seg];

  float s1 = a.s1 + (b.s1 - a.s1) * t;
  float s2 = a.s2 + (b.s2 - a.s2) * t;
  servos.setTargetsRad(s1, s2);
}

// ------------------------------------------------------------------
// 状态机
// ------------------------------------------------------------------
void updateStateMachine() {
  uint32_t now = millis();
  const JuxiImuData &d = imu.data();
  float tilt = d.tiltRad;

  switch (state) {
    case ST_IDLE:
      if (!autoMode) break;
#if USE_RL_POLICY || GETUP_SEQ_READY
      if (tilt > FALL_TILT_RAD) {
        enterState(ST_FALLEN_CONFIRM);
      }
#endif
      break;

    case ST_FALLEN_CONFIRM:
      if (tilt < DONE_TILT_RAD) {
        enterState(ST_IDLE);
      } else if (now - fallStart >= FALL_CONFIRM_MS) {
        if (!startGetup()) enterState(ST_IDLE);
      }
      break;

    case ST_GETUP: {
#if USE_RL_POLICY
      policyRunner.step(d, servos);
#else
      updateGetupTargets();
#endif

      if (tilt < DONE_TILT_RAD) {
        if (uprightStart == 0) uprightStart = now;
        if (now - uprightStart >= DONE_HOLD_MS) {
          enterState(ST_HOLD);
        }
      } else {
        uprightStart = 0;
      }

      if (now - getupStart > GETUP_TIMEOUT_MS) {
        Serial.println("GETUP timeout -> ABORT");
        enterState(ST_ABORT);
      }
      break;
    }

    case ST_HOLD:
      if (now - stateStart >= GETUP_HOLD_MS) {
        enterState(ST_DONE);
      }
      break;

    case ST_DONE:
      Serial.printf("GETUP done: pose=%s\n", poseName(pose));
      attempts = 0;
      enterState(ST_IDLE);
      break;

    case ST_ABORT:
      if (now - abortStart >= AUTO_RETRY_COOLDOWN_MS) {
        if (autoMode && attempts < AUTO_RETRY_MAX && tilt > FALL_TILT_RAD) {
          startGetup();
        } else {
          attempts = 0;
          enterState(ST_IDLE);
        }
      }
      break;

    case ST_FAULT:
      // 等待串口 r 复位
      break;

    case ST_MANUAL:
    case ST_BOOT:
    case ST_SELFTEST:
    default:
      break;
  }
}

// IMU 失效保护：每个控制周期都调用，不依赖 imu.update() 是否成功
void checkImuTimeout() {
  uint32_t now = millis();
  if (now - lastImuGood <= IMU_FAIL_TIMEOUT_MS) return;

  if (state == ST_GETUP || state == ST_HOLD || state == ST_FALLEN_CONFIRM) {
    Serial.println("IMU timeout during motion -> ABORT");
    enterState(ST_ABORT);
  } else if (state != ST_FAULT && now - lastImuGood > 2000) {
    Serial.println("IMU timeout -> FAULT");
    enterState(ST_FAULT);
  }
}

// ------------------------------------------------------------------
// 手动/串口
// ------------------------------------------------------------------
void printHelp() {
  Serial.println("命令: g=起立 x=急停 r=复位 m=手动/自动 p=状态 s=舵机状态");
  Serial.println("      1-8=选择舵机 a/d=选中舵机 -/+5° j/l=舵机2 -/+5° c=回中 v=详细 ?=帮助");
}

void printStatus() {
  const JuxiImuData &d = imu.data();
  Serial.printf("state=%s pose=%s driver=%s sel=CH%u tilt=%.1f° roll=%.1f° pitch=%.1f° "
                "s1=%.1f°/%.1f° s2=%.1f°/%.1f° attempts=%u imu=%d\n",
                stateName(state), poseName(pose), servos.driverName(),
                (unsigned)(selectedChannel + 1),
                d.tiltRad * RAD_TO_DEG, d.rollDeg, d.pitchDeg,
                servos.target1() * RAD_TO_DEG, servos.current1() * RAD_TO_DEG,
                servos.target2() * RAD_TO_DEG, servos.current2() * RAD_TO_DEG,
                (unsigned)attempts, d.valid ? 1 : 0);
}

void printServoStatus() {
  Serial.printf("driver=%s ok=%d attached=%d channels=%d\n",
                servos.driverName(), servos.driverOk() ? 1 : 0,
                servos.attached() ? 1 : 0, SERVO_COUNT);
  for (uint8_t ch = 0; ch < SERVO_COUNT; ch++) {
#if SERVO_DRIVER_MODE == 2
    Serial.printf("  CH%u %-8s target=%6.1f° current=%6.1f°\n",
                  (unsigned)(ch + 1), servoRoleName(ch),
                  servos.targetRad(ch) * RAD_TO_DEG,
                  servos.currentRad(ch) * RAD_TO_DEG);
#else
    Serial.printf("  CH%u GPIO%u %-8s target=%6.1f° current=%6.1f°\n",
                  (unsigned)(ch + 1), (unsigned)SERVO_PINS[ch], servoRoleName(ch),
                  servos.targetRad(ch) * RAD_TO_DEG,
                  servos.currentRad(ch) * RAD_TO_DEG);
#endif
  }
}

void printCsv() {
  const JuxiImuData &d = imu.data();
  Serial.printf("%s,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%d,%d\n",
                stateName(state),
                d.tiltRad * RAD_TO_DEG,
                d.rollDeg, d.pitchDeg,
                servos.target1() * RAD_TO_DEG, servos.current1() * RAD_TO_DEG,
                servos.target2() * RAD_TO_DEG, servos.current2() * RAD_TO_DEG,
                attempts, d.valid ? 1 : 0);
}

void manualMoveChannel(uint8_t ch, float deltaRad) {
  if (state != ST_MANUAL) {
    Serial.println("先按 m 进入手动模式");
    return;
  }
  if (ch >= SERVO_COUNT) return;
  servos.moveChannelDeltaRad(ch, deltaRad);
  Serial.printf("manual: CH%u=%.1f°\n", (unsigned)(ch + 1),
                servos.targetRad(ch) * RAD_TO_DEG);
}

void handleCommand(char c) {
  switch (c) {
    case 'g':
      if (state == ST_FAULT) {
        Serial.println("FAULT: 先按 r 复位");
      } else if (state == ST_GETUP || state == ST_HOLD) {
        Serial.println("已经在起立中");
      } else {
        startGetup();
      }
      break;

    case 'x':
      Serial.println("急停");
      servos.stop();
      enterState(ST_FAULT);
      break;

    case 'r':
      attempts = 0;
      pose = POSE_UNKNOWN;
      servos.stop();
      imuReady = imu.begin();
      if (!imuReady) {
        Serial.println("IMU 重新初始化失败：检查 0x23/100kHz/3.3V/共地");
        enterState(ST_FAULT);
        break;
      }
      if (!servos.begin()) {
        Serial.println("舵机驱动重新初始化失败：检查转接板/电源/I2C 地址");
        enterState(ST_FAULT);
        break;
      }
      servos.centerImmediate();
      lastImuGood = millis();
      enterState(ST_IDLE);
      Serial.println("已复位");
      break;

    case 'm':
      if (state == ST_FAULT) {
        Serial.println("FAULT: 先按 r 复位");
        break;
      }
      autoMode = !autoMode;
      if (autoMode) {
        enterState(ST_IDLE);
      } else {
        enterState(ST_MANUAL);
      }
      Serial.printf("自动模式: %s\n", autoMode ? "开" : "关");
      break;

    case 'p':
      printStatus();
      break;

    case 's':
      printServoStatus();
      break;

    case 'c':
      if (state == ST_FAULT) {
        Serial.println("FAULT: 先按 r 复位");
        break;
      }
      servos.centerAllSlow();
      Serial.println("所有通道回中（慢速）");
      break;

    case '1': case '2': case '3': case '4':
    case '5': case '6': case '7': case '8':
      selectedChannel = (uint8_t)(c - '1');
      Serial.printf("选择 CH%u (%s)\n", (unsigned)(selectedChannel + 1),
                    servoRoleName(selectedChannel));
      break;

    case 'a': manualMoveChannel(selectedChannel, -5.0f * DEG_TO_RAD); break;
    case 'd': manualMoveChannel(selectedChannel, +5.0f * DEG_TO_RAD); break;
    case 'j': manualMoveChannel(1, -5.0f * DEG_TO_RAD); break;
    case 'l': manualMoveChannel(1, +5.0f * DEG_TO_RAD); break;

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

void handleButton() {
#if PIN_BUTTON < 0
  return;
#else
  bool pressed = (digitalRead(PIN_BUTTON) == LOW);
  uint32_t now = millis();
  if (pressed && !buttonPrev && now - lastButtonMs > 50) {
    lastButtonMs = now;
    if (state == ST_GETUP || state == ST_HOLD) {
      Serial.println("按钮急停");
      servos.stop();
      enterState(ST_FAULT);
    } else if (state == ST_IDLE) {
      startGetup();
    }
  }
  buttonPrev = pressed;
#endif
}

// ------------------------------------------------------------------
// setup / loop
// ------------------------------------------------------------------
void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1000);
  Serial.println();
  Serial.println("SR-Support 2-DOF slow getup (ESP32-S3 + Juxi IMU + PTK 7452MG)");
  Serial.println("独立实现，未复制 SelfRisingRobot；许可见 docs/licensing.md");
  Serial.println("骨架版本：waypoint 仍是占位，先跑 IMU/舵机/手动模式。");
  printHelp();

#if PIN_BUTTON >= 0
  pinMode(PIN_BUTTON, INPUT_PULLUP);
#endif

#if SERVO_DRIVER_MODE == 2
  Serial.println("舵机驱动: PCA9685/I2C");
#else
  Serial.println("舵机驱动: LEDC 直连 GPIO");
#endif

  // 先确认 IMU 正常，再驱动舵机；IMU 失败时不输出 PWM。
  Serial.printf("等待 IMU 启动 %d ms...\n", IMU_STARTUP_MS);
  for (int i = IMU_STARTUP_MS / 1000; i > 0; i--) {
    Serial.printf("%d...\n", i);
    delay(1000);
  }

  imuReady = imu.begin();
  if (!imuReady) {
    Serial.println("IMU 初始化失败：检查 0x23/100kHz/3.3V/共地");
    enterState(ST_FAULT);
    return;
  }

  if (!servos.begin()) {
    Serial.println("舵机驱动初始化失败：检查转接板/电源/I2C 地址 0x40");
    enterState(ST_FAULT);
    return;
  }
  servos.centerImmediate();

  Serial.printf("IMU 版本: v%u.%u.%u\n", (unsigned)imu.data().version[0],
                (unsigned)imu.data().version[1], (unsigned)imu.data().version[2]);

  lastImuGood = millis();
  lastControl = millis();
  lastPrint = millis();
  enterState(ST_IDLE);
  Serial.println("就绪：g 起立 / m 手动 / s 舵机状态 / p 状态 / x 急停");
}

void loop() {
  handleSerial();
  handleButton();

  uint32_t now = millis();
  if (now - lastControl >= CONTROL_PERIOD_MS) {
    lastControl = now;

    if (imuReady) {
      bool ok = imu.update();
      if (ok) {
        lastImuGood = now;
        updateStateMachine();
      }
    }
    checkImuTimeout();

    servos.update();

    if (verbose && now - lastPrint >= PRINT_PERIOD_MS) {
      lastPrint = now;
      printCsv();
    }
  }
}
