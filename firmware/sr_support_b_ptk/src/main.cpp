// 2-DOF self-righting robot firmware — B-line (PTK7452MG PWM).
//
// This file is based on the Juxi-Technology/2dof-selfrighting-robot B-line
// firmware (MIT/Apache-2.0). See third_party/juxi-2dof/ for attribution.
// Local changes: PTK7452MG notes/config, LEDC core 2.x/3.x compatibility, and
// an explicit 'x' PWM-release command.
//
// Pipeline (50 Hz):
//   Juxi ICM42670P (I2C 0x23) -> Mahony filter -> body-frame up + gyro
//   joint state: commanded angle/rate (PTK7452MG has no position feedback)
//   obs = [up(3), gyro(3), q(2), qdot(2)] -> 128x128 tanh MLP
//   -> rate-limited joint targets -> PWM backend
//
// The observation layout and constants must match training/b_line/.

#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "servo_backend.h"

#include <stdarg.h>
#if WIFI_TELEMETRY
#include <WiFi.h>
#endif
#include <esp_partition.h>

#ifdef ROBOT_PWM
#include "policy_b.h"
#else
#error "This project is the B-line PWM build; ROBOT_PWM must be defined."
#endif

static_assert(POLICY_OBS_DIM == 10 || POLICY_OBS_DIM == 5,
              "B-line policy must use the 10-D or SR 5-D observation");
static_assert(POLICY_ACT_DIM == 2, "B-line policy must output 2 actions");

static const float PI_F = 3.14159265358979323846f;
// Juxi module scales: int16 spans +/-16 g and +/-2000 dps.
static const float A_SCALE = (16.0f / 32767.0f) * GRAVITY;  // m/s^2 per LSB
static const float G_SCALE = (2000.0f / 32767.0f) * PI_F / 180.0f;  // rad/s

// --------------------------------------------------------------------- IMU
static float g_imu_sign[3] = {1.0f, 1.0f, 1.0f};  // 'i'/'j' axis calibration
static float gyro_bias[3] = {0.0f, 0.0f, 0.0f};
static float g_gyro[3] = {0.0f, 0.0f, 0.0f};  // bias-corrected, body frame
static uint32_t last_imu_ok_ms = 0;

static bool imu_read_regs(uint8_t reg, uint8_t *buf, uint8_t n) {
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom(IMU_I2C_ADDR, n) != n) return false;
    for (uint8_t i = 0; i < n; ++i) buf[i] = (uint8_t)Wire.read();
    return true;
}

// Recover a wedged I2C peripheral: re-create the bus and re-init the IMU.
static void imu_bus_reset() {
    Wire.end();
    delay(5);
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(IMU_I2C_HZ);
    Wire.setTimeOut(50);   // never block forever on a wedged I2C bus
    delay(5);
}

// 0x04..0x0F are contiguous: accel XYZ then gyro XYZ, little-endian int16.
static bool imu_read_raw(int16_t raw[6]) {
    uint8_t buf[12];
    if (!imu_read_regs(0x04, buf, sizeof(buf))) return false;
    for (int i = 0; i < 6; ++i) {
        raw[i] = (int16_t)((uint16_t)buf[2 * i] | ((uint16_t)buf[2 * i + 1] << 8));
    }
    return true;
}

static void raw_to_si(const int16_t raw[6], float acc[3], float gyro[3]) {
    // IMU AXES: the module is mounted with its printed +X forward, +Y left
    // and +Z up. The 'i'/'j' commands flip X/Y at runtime for calibration.
    acc[0] = raw[0] * A_SCALE * g_imu_sign[0];
    acc[1] = raw[1] * A_SCALE * g_imu_sign[1];
    acc[2] = raw[2] * A_SCALE * g_imu_sign[2];
    gyro[0] = raw[3] * G_SCALE * g_imu_sign[0] - gyro_bias[0];
    gyro[1] = raw[4] * G_SCALE * g_imu_sign[1] - gyro_bias[1];
    gyro[2] = raw[5] * G_SCALE * g_imu_sign[2] - gyro_bias[2];
}

static bool imu_init() {
    // The module can need longer than the 5 s startup delay after a warm
    // reset, and a single version read can return 0.0.0 while it is still
    // booting. Retry for up to 10 s instead of failing on the first read.
    uint32_t start = millis();
    uint8_t ver[3];
    bool printed_wait = false;
    while (millis() - start < 10000) {
        if (imu_read_regs(0x01, ver, sizeof(ver))) {
            if (!((ver[0] == 0x00 && ver[1] == 0x00 && ver[2] == 0x00) ||
                  (ver[0] == 0xFF && ver[1] == 0xFF && ver[2] == 0xFF))) {
                Serial.printf("IMU version %u.%u.%u\n", ver[0], ver[1], ver[2]);
                return true;
            }
        }
        if (!printed_wait) {
            Serial.println("IMU not ready; retrying for up to 10 s...");
            printed_wait = true;
        }
        delay(200);
    }
    return false;
}

static bool calibrate_gyro() {
    const int N = 2000;
    double sum[3] = {0.0, 0.0, 0.0};
    int n = 0;
    uint32_t start = millis();
    while (n < N && (millis() - start) < 5000) {
        int16_t raw[6];
        if (imu_read_raw(raw)) {
            sum[0] += raw[3];
            sum[1] += raw[4];
            sum[2] += raw[5];
            ++n;
        }
        delay(1);
    }
    if (n < N / 2) return false;
    for (int i = 0; i < 3; ++i) gyro_bias[i] = (float)(sum[i] / n) * G_SCALE;
    Serial.printf("gyro bias (rad/s): %.4f %.4f %.4f\n",
                  gyro_bias[0], gyro_bias[1], gyro_bias[2]);
    return true;
}

// -------------------------------------------------------- Mahony attitude filter
// q maps body -> world, stored as (w, x, y, z).
static float q_att[4] = {1.0f, 0.0f, 0.0f, 0.0f};
static float mahony_i[3] = {0.0f, 0.0f, 0.0f};

static void mahony_update(const float gyro[3], const float acc[3], float dt) {
    float ax = acc[0], ay = acc[1], az = acc[2];
    float an = sqrtf(ax * ax + ay * ay + az * az);
    float ex = 0.0f, ey = 0.0f, ez = 0.0f;

    if (an > 1e-3f) {
        ax /= an;
        ay /= an;
        az /= an;
        if (fabsf(an - GRAVITY) < ACCEL_TRUST_BAND) {
            // Predicted world-up in body frame = R^T e_z = third row of R.
            float vx = 2.0f * (q_att[1] * q_att[3] - q_att[0] * q_att[2]);
            float vy = 2.0f * (q_att[2] * q_att[3] + q_att[0] * q_att[1]);
            float vz = 1.0f - 2.0f * (q_att[1] * q_att[1] + q_att[2] * q_att[2]);
            ex = ay * vz - az * vy;
            ey = az * vx - ax * vz;
            ez = ax * vy - ay * vx;
        }
    }

    mahony_i[0] += ex * dt;
    mahony_i[1] += ey * dt;
    mahony_i[2] += ez * dt;

    float gx = gyro[0] + MAHONY_KP * ex + MAHONY_KI * mahony_i[0];
    float gy = gyro[1] + MAHONY_KP * ey + MAHONY_KI * mahony_i[1];
    float gz = gyro[2] + MAHONY_KP * ez + MAHONY_KI * mahony_i[2];

    float qw = q_att[0], qx = q_att[1], qy = q_att[2], qz = q_att[3];
    q_att[0] += 0.5f * dt * (-qx * gx - qy * gy - qz * gz);
    q_att[1] += 0.5f * dt * (qw * gx + qy * gz - qz * gy);
    q_att[2] += 0.5f * dt * (qw * gy - qx * gz + qz * gx);
    q_att[3] += 0.5f * dt * (qw * gz + qx * gy - qy * gx);

    float n = sqrtf(q_att[0] * q_att[0] + q_att[1] * q_att[1] +
                    q_att[2] * q_att[2] + q_att[3] * q_att[3]);
    if (n > 1e-9f) {
        for (int i = 0; i < 4; ++i) q_att[i] /= n;
    }
}

static void up_body(float u[3]) {
    const float ux = 2.0f * (q_att[1] * q_att[3] - q_att[0] * q_att[2]);
    const float uy = 2.0f * (q_att[2] * q_att[3] + q_att[0] * q_att[1]);
    const float uz = 1.0f - 2.0f * (q_att[1] * q_att[1] + q_att[2] * q_att[2]);
#if IMU_YAW90
    // IMU mounted 90 deg about the body vertical (see config.h).
    u[0] = uy;
    u[1] = -ux;
    u[2] = uz;
#else
    u[0] = ux;
    u[1] = uy;
    u[2] = uz;
#endif
}

// -------------------------------------------------- offline telemetry, wifi
// RAM ring buffer of compact state lines, dumped over serial with 'L':
// run the robot on battery, then plug in USB and dump the last ~40 s.
// The same lines also stream to a TCP client at 192.168.4.1:3333 while the
// WiFi AP is on ('w' toggles it; it is on after boot by default).
static char sr_log_buf[SR_LOG_RING_BYTES];
static uint32_t sr_log_w = 0;
static uint32_t sr_log_total = 0;

static void sr_snap_save();   // flash snapshot (defined with the log dump)

static void sr_log_puts(const char *s) {
    while (*s) {
        sr_log_buf[sr_log_w] = *s++;
        sr_log_w = (sr_log_w + 1u) % SR_LOG_RING_BYTES;
        ++sr_log_total;
    }
}

#if WIFI_TELEMETRY
static WiFiServer twin_srv(3333);
#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
static NetworkClient twin_cli;
#else
static WiFiClient twin_cli;
#endif
static bool wifi_on = false;

static void wifi_begin() {
    if (wifi_on) return;
    if (WiFi.getMode() == WIFI_OFF) {
        WiFi.mode(WIFI_AP);
    }
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS);
    twin_srv.begin();
    twin_srv.setNoDelay(true);
    wifi_on = true;
    Serial.printf("wifi ap '%s' pass '%s' ip %s tcp 3333\n",
                  WIFI_AP_SSID, WIFI_AP_PASS,
                  WiFi.softAPIP().toString().c_str());
}

static void wifi_stop() {
    if (!wifi_on) return;
    twin_cli.stop();
    twin_srv.stop();
    WiFi.softAPdisconnect(true);
    // keep the driver initialised: a full WiFi.mode(WIFI_OFF) makes
    // the next re-init fail inside ESP-IDF (netstack cb reg error)
    wifi_on = false;
    Serial.println("wifi off ('w' re-enables)");
}
#endif

// One telemetry line: always into the RAM ring, to the wifi client if any.
static void tel_emit(const char *line) {
    sr_log_puts(line);
#if WIFI_TELEMETRY
    if (wifi_on) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
        NetworkClient nc = twin_srv.accept();
#else
        WiFiClient nc = twin_srv.available();
#endif
        if (nc) {
            twin_cli.stop();
            twin_cli = nc;
            twin_cli.setNoDelay(true);
            Serial.println("wifi telemetry client connected");
        }
        if (twin_cli && twin_cli.connected()) {
            twin_cli.write((const uint8_t *)line, strlen(line));
        }
    }
#endif
}

// -------------------------------------------------------------------- control
static float cmd[2] = {0.0f, 0.0f};       // last commanded joint angles, rad
static float qdot_cmd[2] = {0.0f, 0.0f};  // last command rate, rad/s
static float q_obs[2] = {0.0f, 0.0f};     // joint state fed to the policy
static float qd_obs[2] = {0.0f, 0.0f};
static bool running = false;
static bool manual = false;                 // 1/2/3/4/0 single-joint test mode
static float manual_target[2] = {0.0f, 0.0f};
static uint8_t stand_state = 0;             // 0 = policy, 1 = homing, 2 = stand
static uint8_t stand_hold = 0;              // consecutive upright control steps
static bool home_enable = true;             // 'h' toggles the stand homing
static bool policy_armed = false;           // only run the policy after a full fall
static uint8_t fall_ticks = 0;              // consecutive up_z < 0.5
static uint16_t stand_ticks = 0;            // consecutive upright after homing
static float act_filt[2] = {0.0f, 0.0f};   // low-passed policy action
static bool auto_mode = false;              // scripted get-up mode ('a')
static uint8_t auto_state = 0;              // 0 idle, 1 sequence, 2 home
static uint8_t auto_idx = 0;
static uint16_t auto_ticks = 0;
static uint8_t auto_fall = 0;
static const float AUTO_SEQ[6][2] = {
    {0.50f, -1.55f}, {-1.55f, -1.55f}, {-1.55f, 1.55f},
    {1.55f, -1.55f}, {1.55f, 0.00f}, {-0.50f, -1.55f},
};
static const uint16_t AUTO_HOLD = 65;       // 1.3 s at 50 Hz
static bool fast_log = false;
static uint32_t fast_log_until = 0;
static bool twin_log = false;   // 'd': 50 Hz T stream for the MuJoCo live twin
static int16_t g_raw[6] = {0};
static int servo_fail_count = 0;
static uint32_t next_ctrl_us = 0;

static float clampf(float x, float lo, float hi) {
    return x < lo ? lo : (x > hi ? hi : x);
}

static void manual_step() {
    float next[2];
    for (int i = 0; i < 2; ++i) {
        next[i] = clampf(manual_target[i], cmd[i] - MAX_CMD_RATE, cmd[i] + MAX_CMD_RATE);
        qdot_cmd[i] = (next[i] - cmd[i]) / POLICY_DT;
        cmd[i] = next[i];
        q_obs[i] = next[i];
        qd_obs[i] = qdot_cmd[i];
    }
    servo::write(cmd);
}

static void auto_next(float next[2], float up_z) {
    float target[2] = {0.0f, 0.0f};
    if (auto_state == 0) {
        if (up_z < 0.50f) {
            if (++auto_fall >= 25) {
                auto_state = 1;
                auto_idx = 0;
                auto_ticks = 0;
                auto_fall = 0;
                Serial.println("auto: fallen -> scripted get-up");
            }
        } else {
            auto_fall = 0;
        }
    } else if (auto_state == 1) {
        target[0] = AUTO_SEQ[auto_idx][0];
        target[1] = AUTO_SEQ[auto_idx][1];
        if (++auto_ticks >= AUTO_HOLD) {
            auto_ticks = 0;
            if (++auto_idx >= 6) {
                auto_state = 2;
                auto_fall = 0;
                Serial.println("auto: sequence done -> home");
            }
        }
    } else {
        if (up_z < 0.50f) {
            if (++auto_fall >= 50) {
                auto_state = 1;
                auto_idx = 0;
                auto_ticks = 0;
                auto_fall = 0;
                Serial.println("auto: still fallen -> retry");
            }
        } else if (up_z > 0.90f) {
            if (++auto_fall >= 25) {
                auto_state = 0;
                auto_fall = 0;
                Serial.println("auto: standing");
            }
        } else {
            auto_fall = 0;
        }
    }
    for (int i = 0; i < 2; ++i) {
        next[i] = clampf(target[i], cmd[i] - MAX_CMD_RATE, cmd[i] + MAX_CMD_RATE);
    }
}

// ------------------------------------- deterministic reference get-up
// The pitch sequences were searched in MuJoCo (tools/search_b39_getup.py) on
// the 4 cm b39 model. The executor is the same algorithm as
// training/b_line/getup_executor.py:
//   - 20 control ticks per waypoint, linear target interpolation;
//   - final phase retracts the arm to neutral at a constant rate;
//   - a settled pose on another lying axis re-plans (neutral + new
//     reference) instead of running the wrong sequence to the timeout.
// The roll_pos sequence (arm swept to +2.0 rad with the elbow at -0.8) is
// the one that works on the real robot. The servo PWM output is clamped to
// SERVO_MAX_US, so the arm physically tops out near +1.04 rad even though
// the config range says +2.07 - the real machine gets up with that reduced
// travel, i.e. the usable range is nearly symmetric [-1.07, +1.04]. The
// roll_neg get-up is therefore the MIRROR of the roll_pos press (a pose
// rotation of 180 deg about the shoulder axis maps q1 -> q1 + pi, so the
// +2.0 press mirrors to -1.14, just past the -1.07 stop): press the
// shoulder to -1.07 with the elbow folded the mirrored way and hold; the
// arm levers the lying body straight up onto its base, no roll-over.
// (The previous over-the-top roll recipe needed the +X-side travel that
// the PWM clamp removes; it stalls at a 150 deg equilibrium, see
// docs/hardware-validation.md 0.4.)
//
// With the servo rail at 5 V the shoulder-only press stalls at about
// up_z 0.60 (torque-marginal near the base-rim lever); the same press
// succeeded on the 6 V bench. The sequence therefore adds a second motor
// and an impact: lift the arm off the floor, slam into the press, then
// pump ELBOW WEDGES (shoulder held at the stop, elbow 0.8 -> 0.15 -> 0.8
// re-fold). Kinematic probe at the recorded stall attitude
// (tools/probe_v1_kick_geometry.py): extending the elbow drives the forearm tip deeper
// toward the floor and lengthens the contact lever while the shoulder q1
// reaction is zero, so the floor reaction lifts the body exactly where the
// static press runs out of torque; the re-fold only slides the tip inward
// (the rim holds the body), so the wedges ratchet without giving height
// back. Adaptive per-phase holds and the mid-sequence upright exit live in
// exec_step (EXEC_R1_HOLD).
static const float EXEC_REF0[3][2] = {   // roll_pos
    {2.0f, -0.8f}, {0.0f, -0.8f}, {0.0f, 0.0f}};
static const float EXEC_REF1[13][2] = {  // roll_neg: slam, press, elbow wedges
    {0.6f, 0.8f},   {0.6f, 0.8f},    // wind-up off the floor, brake
    {-1.07f, 0.8f},                  // slam into the press
    {-1.07f, 0.8f},                  // adaptive press hold
    {-1.07f, 0.15f},                 // elbow wedge 1 (forearm pushes up)
    {-1.07f, 0.15f},                 // adaptive hold
    {-1.07f, 0.8f},                  // re-fold (re-cock the elbow)
    {-1.07f, 0.15f},                 // elbow wedge 2
    {-1.07f, 0.15f},                 // adaptive hold
    {-1.07f, 0.8f},                  // re-fold
    {-1.07f, 0.15f},                 // elbow wedge 3
    {-1.07f, 0.15f},                 // final hold
    {0.0f, 0.0f}};                   // retract
static const float EXEC_REF2[3][2] = {   // pitch_pos
    {-1.07f, 1.55f}, {0.0f, 1.55f}, {0.0f, 0.0f}};
static const float EXEC_REF3[3][2] = {   // pitch_neg
    {-1.07f, -1.55f}, {0.0f, -1.55f}, {0.0f, 0.0f}};
static const float *const EXEC_REFS[4] = {
    (const float *)EXEC_REF0, (const float *)EXEC_REF1,
    (const float *)EXEC_REF2, (const float *)EXEC_REF3};
static const uint8_t EXEC_REF_N[4] = {3, 13, 3, 3};
// Per-phase adaptive-hold caps (ticks) for roll_neg: a capped phase holds
// while the body is still down (up_z < 0.92) and advances once upright or
// when the cap expires, so a stalled mechanism hands over to the next one
// instead of eating the whole timeout.
static const uint16_t EXEC_R1_HOLD[13] = {
    0, 0, 0, 50, 0, 40, 0, 0, 40, 0, 0, 100, 0};
static const char *const EXEC_POSE_NAMES[4] = {
    "roll_pos", "roll_neg", "pitch_pos", "pitch_neg"};

static bool exec_running = false;
static bool exec_neutral = false;
static uint8_t exec_pose = 0;
static int8_t exec_pending_pose = 0;
static uint8_t exec_phase = 0;
static uint16_t exec_tick = 0;
static uint16_t exec_stand = 0;
static uint16_t exec_cooldown = 0;
static uint16_t exec_age = 0;
static uint16_t exec_neutral_ticks = 0;
static uint8_t exec_switches = 0;
static uint8_t exec_other_ticks = 0;
static uint8_t exec_trace_div = 0;
static uint32_t exec_start_ms = 0;
static float exec_prev[2] = {0.0f, 0.0f};
static float exec_target[2] = {0.0f, 0.0f};

static int pose_from_up(float ux, float uy) {
    if (fabsf(ux) >= fabsf(uy)) return (ux < 0.0f) ? 2 : 3;  // pitch
    return (uy > 0.0f) ? 0 : 1;                              // roll
}

// Load a reference and start it from the current joint command: after a
// failed attempt the arm can be parked at a previous support waypoint.
static void exec_load(int pose) {
    exec_pose = (uint8_t)pose;
    exec_phase = 0;
    exec_tick = 0;
    exec_prev[0] = exec_target[0] = cmd[0];
    exec_prev[1] = exec_target[1] = cmd[1];
    exec_running = true;
    exec_stand = 0;
    exec_age = 0;
    exec_other_ticks = 0;
    exec_start_ms = millis();
}

static void exec_start(int pose) {
    exec_neutral = false;
    exec_neutral_ticks = 0;
    exec_switches = 0;
    exec_cooldown = 0;
    exec_load(pose);
    {
        char l[24];
        snprintf(l, sizeof l, "E start %u\n", (unsigned)pose);
        tel_emit(l);
    }
}

static void exec_step(float next[2], const float u[3]) {
    if (!exec_running) {
        next[0] = next[1] = 0.0f;
        return;
    }
    if ((uint32_t)(millis() - exec_start_ms) > EXEC_TIMEOUT_MS) {
        exec_running = false;
        policy_armed = false;
        exec_cooldown = EXEC_COOLDOWN_TICKS;
        next[0] = next[1] = 0.0f;
        Serial.println("executor timeout");
        tel_emit("E timeout\n");
        sr_snap_save();
        return;
    }
    ++exec_age;
    if (++exec_trace_div >= 10) {
        exec_trace_div = 0;
        Serial.printf("executor pose=%s ph=%u tick=%u tgt=(%.2f,%.2f) "
                      "up=(%.2f,%.2f,%.2f) q=(%.2f,%.2f) sw=%u\n",
                      EXEC_POSE_NAMES[exec_pose], exec_phase, exec_tick,
                      exec_target[0], exec_target[1], u[0], u[1], u[2],
                      cmd[0], cmd[1], exec_switches);
    }
    if (exec_neutral) {
        // Retract both joints to neutral before the re-planned reference.
        bool at_zero = true;
        for (int i = 0; i < 2; ++i) {
            exec_target[i] += clampf(-exec_target[i],
                                     -EXEC_RETRACT_RATE, EXEC_RETRACT_RATE);
            if (fabsf(exec_target[i]) < 0.02f) {
                exec_target[i] = 0.0f;
            } else {
                at_zero = false;
            }
            next[i] = clampf(exec_target[i], cmd[i] - MAX_CMD_RATE,
                             cmd[i] + MAX_CMD_RATE);
        }
        if (at_zero || ++exec_neutral_ticks > EXEC_NEUTRAL_MAX) {
            exec_neutral = false;
            exec_neutral_ticks = 0;
            exec_load(exec_pending_pose);
        }
        return;
    }
    {
        const float w_arm = sqrtf(g_gyro[0] * g_gyro[0] +
                                  g_gyro[1] * g_gyro[1] +
                                  g_gyro[2] * g_gyro[2]);
        bool switching = false;
        if (exec_age >= EXEC_MIN_SWITCH_AGE && u[2] < EXEC_SWITCH_UP &&
            w_arm < EXEC_SWITCH_W && exec_switches < EXEC_MAX_SWITCHES) {
            const int cand = pose_from_up(u[0], u[1]);
            if (cand != (int)exec_pose) {
                if (++exec_other_ticks >= EXEC_SWITCH_TICKS) {
                    exec_other_ticks = 0;
                    ++exec_switches;
                    exec_pending_pose = (int8_t)cand;
                    exec_neutral = true;
                    exec_neutral_ticks = 0;
                    Serial.printf("executor re-plan %s -> %s "
                                  "up=(%.2f,%.2f,%.2f)\n",
                                  EXEC_POSE_NAMES[exec_pose],
                                  EXEC_POSE_NAMES[cand], u[0], u[1], u[2]);
                    {
                        char l[24];
                        snprintf(l, sizeof l, "E replan %u %u\n",
                                 (unsigned)exec_pose, (unsigned)cand);
                        tel_emit(l);
                    }
                    switching = true;
                }
            } else {
                exec_other_ticks = 0;
            }
        } else {
            exec_other_ticks = 0;
        }
        if (switching) {
            next[0] = clampf(exec_target[0], cmd[0] - MAX_CMD_RATE,
                             cmd[0] + MAX_CMD_RATE);
            next[1] = clampf(exec_target[1], cmd[1] - MAX_CMD_RATE,
                             cmd[1] + MAX_CMD_RATE);
            return;
        }
    }
    const float *seq = EXEC_REFS[exec_pose];
    const uint8_t n = EXEC_REF_N[exec_pose];
    // roll_neg got upright mid-sequence: skip the remaining hammer / wedge
    // stages (they would knock the standing body over) and retract now.
    if (exec_pose == 1 && u[2] > 0.92f && exec_phase < (uint8_t)(n - 1)) {
        exec_phase = (uint8_t)(n - 1);
        exec_tick = 0;
    }
    if (exec_phase < (uint8_t)(n - 1)) {
        // exec_tick keeps counting past EXEC_STEPS_PER_WP while a capped
        // roll_neg phase holds; frac is clamped, so the extra ticks only
        // feed the EXEC_R1_HOLD cap check.
        ++exec_tick;
        float frac = (float)exec_tick / (float)EXEC_STEPS_PER_WP;
        if (frac > 1.0f) frac = 1.0f;
        for (int i = 0; i < 2; ++i) {
            const float wp = seq[(int)exec_phase * 2 + i];
            exec_target[i] = exec_prev[i] + (wp - exec_prev[i]) * frac;
        }
        if (exec_tick >= EXEC_STEPS_PER_WP) {
            // Capped roll_neg phases wait for the body to come up
            // (up_z < 0.92) but hand over to the next mechanism when the
            // cap expires; all other phases advance every 20 ticks.
            bool hold = false;
            if (exec_pose == 1 && u[2] < 0.92f) {
                const uint16_t cap = EXEC_R1_HOLD[exec_phase];
                hold = (cap > 0) && (exec_tick < cap);
            }
            if (!hold) {
                for (int i = 0; i < 2; ++i) {
                    exec_prev[i] = seq[(int)exec_phase * 2 + i];
                }
                ++exec_phase;
                exec_tick = 0;
            }
        }
    } else {
        // Final phase: retract to neutral at a constant rate. The retract is
        // itself a lift in several poses, so it runs unconditionally; a
        // topple is handled by the pose re-plan / fall gate.
        for (int i = 0; i < 2; ++i) {
            exec_target[i] += clampf(-exec_target[i],
                                     -EXEC_RETRACT_RATE, EXEC_RETRACT_RATE);
        }
        if (fabsf(exec_target[0]) < 0.02f && fabsf(exec_target[1]) < 0.02f) {
            exec_target[0] = exec_target[1] = 0.0f;
        }
    }
    // Same per-tick slew limit as the sim executor's 0.08 rad action delta.
    for (int i = 0; i < 2; ++i) {
        next[i] = clampf(exec_target[i], cmd[i] - MAX_CMD_RATE,
                         cmd[i] + MAX_CMD_RATE);
    }

    const bool done = (u[2] > 0.95f) &&
                      (fabsf(exec_target[0]) < 0.02f) &&
                      (fabsf(exec_target[1]) < 0.02f);
    if (done) {
        if (++exec_stand >= EXEC_DONE_TICKS) {
            exec_running = false;
            policy_armed = false;
            exec_cooldown = EXEC_COOLDOWN_TICKS;
            Serial.println("standing -> executor done");
            tel_emit("E done\n");
            sr_snap_save();
        }
    } else {
        exec_stand = 0;
    }
}

static void control_step() {
    if (servo::has_feedback()) {
        if (!servo::read(q_obs, qd_obs)) {
            if (++servo_fail_count > 5) servo::stop();
            return;
        }
        servo_fail_count = 0;
    } else {
        q_obs[0] = cmd[0];
        q_obs[1] = cmd[1];
        qd_obs[0] = qdot_cmd[0];
        qd_obs[1] = qdot_cmd[1];
    }

    float u[3];
    up_body(u);

    float next[2] = {0.0f, 0.0f};
    if (auto_mode) {
        auto_next(next, u[2]);
    } else if (!policy_armed) {
        // Hold neutral until the robot is fully fallen AND at rest; a hand
        // tilt past 60 deg used to arm the policy mid-placement, so the gate
        // is now up_z < 0.35 with a quiet gyro.
        const float w_arm = sqrtf(g_gyro[0] * g_gyro[0] + g_gyro[1] * g_gyro[1] +
                                  g_gyro[2] * g_gyro[2]);
        if (exec_cooldown > 0) {
            --exec_cooldown;
            fall_ticks = 0;
        } else if (u[2] < FALL_UP_Z && w_arm < FALL_W_QUIET) {
            if (++fall_ticks >= FALL_CONFIRM_TICKS) {
                policy_armed = true;
                fall_ticks = 0;
                stand_state = 0;
                stand_hold = 0;
                stand_ticks = 0;
                act_filt[0] = act_filt[1] = 0.0f;
#if POLICY_OBS_DIM == 5
                exec_start(pose_from_up(u[0], u[1]));
                Serial.printf("getup start pose=%s up=(%.2f,%.2f,%.2f)\n",
                              EXEC_POSE_NAMES[exec_pose], u[0], u[1], u[2]);
#else
                Serial.println("fall detected -> policy armed");
#endif
            }
        } else {
            fall_ticks = 0;
        }
        next[0] = next[1] = 0.0f;
    } else {
#if POLICY_OBS_DIM == 5
        // Deterministic reference + feedback get-up executor.
        exec_step(next, u);
#else
        float obs[POLICY_OBS_DIM] = {
            u[0], u[1], u[2],
            g_gyro[0], g_gyro[1], g_gyro[2],
            q_obs[0], q_obs[1],
            qd_obs[0], qd_obs[1],
        };
        float act[POLICY_ACT_DIM];
        policy_forward(obs, act);

        for (int i = 0; i < 2; ++i) {
            act_filt[i] += ACT_FILTER_ALPHA * (act[i] - act_filt[i]);
            float target = clampf(act_filt[i], -1.0f, 1.0f) * Q_HALF_RANGE;
            next[i] = clampf(target, cmd[i] - MAX_CMD_RATE, cmd[i] + MAX_CMD_RATE);
        }
#endif

#if POLICY_OBS_DIM == 5
        // Get-up is the deterministic reference+feedback executor above.
#else
        // Stand homing: after 0.2 s upright, ramp both targets to zero (the
        // arm vertical pose) at the max slew. Tilt pauses the ramp; a fall
        // hands control back to the policy for another get-up attempt.
        if (home_enable && stand_state != 0) {
            if (u[2] < 0.90f) {
                stand_state = 0;
                stand_hold = 0;
            } else {
                float home[2] = {0.0f, 0.0f};
                if (stand_state == 1) {
                    bool pause = (u[2] < 0.95f);
                    for (int i = 0; i < 2; ++i) {
                        float step = pause ? 0.0f
                                           : clampf(-cmd[i], -MAX_CMD_RATE, MAX_CMD_RATE);
                        home[i] = cmd[i] + step;
                        if (fabsf(home[i]) < 0.02f) home[i] = 0.0f;
                    }
                    if (home[0] == 0.0f && home[1] == 0.0f) stand_state = 2;
                }
                next[0] = home[0];
                next[1] = home[1];
            }
        } else if (home_enable && u[2] > 0.95f &&
                   sqrtf(g_gyro[0] * g_gyro[0] + g_gyro[1] * g_gyro[1] +
                         g_gyro[2] * g_gyro[2]) < 1.5f) {
            if (++stand_hold >= 10) {
                stand_state = 1;
                stand_hold = 0;
            }
        } else {
            stand_hold = 0;
        }

        // Disarm once the stand homing has held the vertical pose for 0.5 s;
        // the next fall re-arms the policy.
        if (stand_state == 2 && u[2] > 0.95f) {
            if (++stand_ticks >= 25) {
                policy_armed = false;
                stand_ticks = 0;
                stand_state = 0;
                Serial.println("standing -> policy disarmed");
            }
        } else {
            stand_ticks = 0;
        }
#endif
    }
    if (!servo::has_feedback()) {
        for (int i = 0; i < 2; ++i) qdot_cmd[i] = (next[i] - cmd[i]) / POLICY_DT;
    }
    for (int i = 0; i < 2; ++i) cmd[i] = next[i];
    servo::write(cmd);
    {
        char l[120];
        snprintf(l, sizeof l,
                 "S %lu %u %u %u %.3f %.3f %.3f %.3f %.3f %.3f %.3f %u "
                 "%.3f %.3f %.3f %.3f\n",
                 (unsigned long)millis(), (unsigned)exec_pose, exec_phase,
                 exec_tick, exec_target[0], exec_target[1], u[0], u[1], u[2],
                 next[0], next[1], exec_switches,
                 q_att[0], q_att[1], q_att[2], q_att[3]);
        tel_emit(l);
    }
}

// ---- flash snapshot of the ring, survives the USB-connect reset ----
#define SNAP_MAGIC 0x53474C31u   // "SGL1"
struct SnapHdr {
    uint32_t magic;
    uint32_t len;
    uint32_t uptime_ms;
};
static const esp_partition_t *snap_partition() {
    const esp_partition_t *q = esp_partition_find_first(
        ESP_PARTITION_TYPE_DATA, ESP_PARTITION_SUBTYPE_DATA_SPIFFS, nullptr);
    if (!q) {
        q = esp_partition_find_first(ESP_PARTITION_TYPE_DATA,
                                     ESP_PARTITION_SUBTYPE_ANY, nullptr);
    }
    return q;
}

static void sr_snap_save() {
    const esp_partition_t *q = snap_partition();
    if (!q || q->size < SR_LOG_RING_BYTES + 64) {
        Serial.println("snapshot: no data partition");
        return;
    }
    static uint32_t last_save_ms = 0;
    if (millis() - last_save_ms < 10000u) return;   // rate limit flash wear
    last_save_ms = millis();
    uint32_t n = sr_log_total < SR_LOG_RING_BYTES ? sr_log_total : SR_LOG_RING_BYTES;
    uint32_t start = (sr_log_total < SR_LOG_RING_BYTES) ? 0u : sr_log_w;
    SnapHdr h = {SNAP_MAGIC, n, millis()};
    uint32_t need = ((sizeof h + n + 4095u) / 4096u) * 4096u;
    esp_partition_erase_range(q, 0, need);
    esp_partition_write(q, 0, &h, sizeof h);
    static uint8_t chunk[4096];
    uint32_t k = 0;
    while (k < n) {
        uint32_t m = (n - k < sizeof chunk) ? (n - k) : (uint32_t)sizeof chunk;
        for (uint32_t i = 0; i < m; ++i) {
            chunk[i] = (uint8_t)sr_log_buf[(start + k + i) % SR_LOG_RING_BYTES];
        }
        uint32_t mw = (m + 3u) & ~3u;
        esp_partition_write(q, sizeof h + k, chunk, mw);
        k += m;
        esp_task_wdt_reset();
    }
    Serial.printf("getup log saved to flash (%lu bytes)\n", (unsigned long)n);
}

static void sr_snap_dump() {
    const esp_partition_t *q = snap_partition();
    SnapHdr h = {0, 0, 0};
    if (q) esp_partition_read(q, 0, &h, sizeof h);
    if (!q || h.magic != SNAP_MAGIC || h.len > SR_LOG_RING_BYTES) {
        Serial.println("no saved getup log in flash");
        return;
    }
    Serial.printf("---slog %lu---\n", (unsigned long)h.len);
    static uint8_t chunk[256];
    uint32_t k = 0;
    while (k < h.len) {
        uint32_t m = (h.len - k < sizeof chunk) ? (h.len - k) : (uint32_t)sizeof chunk;
        esp_partition_read(q, sizeof h + k, chunk, m);
        Serial.write(chunk, m);
        k += m;
        esp_task_wdt_reset();
    }
    Serial.printf("\n---elog---\n");
}

static void sr_log_dump() {
    uint32_t n = sr_log_total < SR_LOG_RING_BYTES ? sr_log_total : SR_LOG_RING_BYTES;
    uint32_t start = (sr_log_total < SR_LOG_RING_BYTES) ? 0u : sr_log_w;
    Serial.printf("---slog %lu---\n", (unsigned long)n);
    char chunk[256];
    uint32_t k = 0;
    while (k < n) {
        uint32_t m = (n - k < (uint32_t)sizeof(chunk)) ? (n - k) : (uint32_t)sizeof(chunk);
        for (uint32_t i = 0; i < m; ++i) {
            chunk[i] = sr_log_buf[(start + k + i) % SR_LOG_RING_BYTES];
        }
        Serial.write((const uint8_t *)chunk, m);
        k += m;
        esp_task_wdt_reset();
    }
    Serial.printf("\n---elog---\n");
}

static void handle_serial() {
    static bool reading_m = false;
    static char mbuf[32];
    static uint8_t mlen = 0;
    while (Serial.available() > 0) {
        char c = (char)Serial.read();
        if (reading_m) {
            if (c == '\n' || c == '\r') {
                mbuf[mlen] = '\0';
                float a, b;
                if (sscanf(mbuf, "%f %f", &a, &b) == 2) {
                    running = false;
                    manual = true;
                    auto_mode = false;
                    stand_state = 0;
                    stand_hold = 0;
                    exec_running = false;
                    exec_cooldown = 0;
                    manual_target[0] = clampf(a, Q_SHOULDER_MIN, Q_SHOULDER_MAX);
                    manual_target[1] = clampf(b, Q_ELBOW_MIN, Q_ELBOW_MAX);
                    next_ctrl_us = micros() + CTRL_PERIOD_US;
                    Serial.printf("manual target q = %.2f %.2f rad\n",
                                  manual_target[0], manual_target[1]);
                } else {
                    Serial.println("usage: m <q1> <q2>");
                }
                reading_m = false;
                mlen = 0;
            } else if (mlen < sizeof(mbuf) - 1) {
                mbuf[mlen++] = c;
            }
            continue;
        }
        if (c == 'm' || c == 'M') {
            reading_m = true;
            mlen = 0;
            continue;
        }
        if (c == 'P') {
            if (exec_running) {
                Serial.println("log dump refused: executor running");
            } else {
                sr_snap_dump();
            }
            continue;
        }
        if (c == 'L') {
            if (exec_running) {
                Serial.println("log dump refused: executor running");
            } else {
                sr_log_dump();
            }
            continue;
        }
        if (c == 'w') {
#if WIFI_TELEMETRY
            if (wifi_on) wifi_stop(); else wifi_begin();
#else
            Serial.println("wifi telemetry not compiled in");
#endif
            continue;
        }
        if (c == 's') {
            running = false;
            manual = false;
            auto_mode = false;
            stand_state = 0;
            stand_hold = 0;
            exec_running = false;
            exec_cooldown = 0;
            servo::stop();
            Serial.println("stopped (holding last target)");
        } else if (c == 'x') {
            running = false;
            manual = false;
            auto_mode = false;
            stand_state = 0;
            stand_hold = 0;
            exec_running = false;
            exec_cooldown = 0;
            servo::release();
            Serial.println("released PWM; cut servo power for a full stop; send r to re-arm");
        } else if (c == 'r') {
            running = false;
            manual = false;
            auto_mode = false;
            stand_state = 0;
            stand_hold = 0;
            exec_running = false;
            exec_cooldown = 0;
            float q0[2];
            if (!servo::begin(q0)) {
                Serial.println("servo re-init failed; check power/wiring");
            } else {
                for (int i = 0; i < 2; ++i) {
                    cmd[i] = q0[i];
                    q_obs[i] = q0[i];
                    qd_obs[i] = 0.0f;
                    qdot_cmd[i] = 0.0f;
                }
                servo_fail_count = 0;
                Serial.println("servo re-armed at neutral; send g to run");
            }
        } else if (c == 'g') {
            manual = false;
            auto_mode = false;
            stand_state = 0;
            stand_hold = 0;
            exec_running = false;
            exec_cooldown = 0;
            policy_armed = false;
            fall_ticks = 0;
            stand_ticks = 0;
            act_filt[0] = act_filt[1] = 0.0f;
            running = true;
            next_ctrl_us = micros() + CTRL_PERIOD_US;
            Serial.println("running");
        } else if (c == 'a') {
            running = false;
            manual = false;
            auto_mode = true;
            stand_state = 0;
            stand_hold = 0;
            exec_running = false;
            exec_cooldown = 0;
            auto_state = 0;
            auto_idx = 0;
            auto_ticks = 0;
            auto_fall = 0;
            next_ctrl_us = micros() + CTRL_PERIOD_US;
            Serial.println("auto righting on (scripted get-up); s to stop");
        } else if (c >= '0' && c <= '4') {
            running = false;
            manual = true;
            auto_mode = false;
            stand_state = 0;
            stand_hold = 0;
            exec_running = false;
            exec_cooldown = 0;
            manual_target[0] = 0.0f;
            manual_target[1] = 0.0f;
            if (c == '1') manual_target[0] = 0.5f;
            if (c == '2') manual_target[0] = -0.5f;
            if (c == '3') manual_target[1] = 0.5f;
            if (c == '4') manual_target[1] = -0.5f;
            next_ctrl_us = micros() + CTRL_PERIOD_US;
            Serial.printf("manual: 1/2 shoulder +/-, 3/4 elbow +/-, 0 neutral -> q %.2f %.2f\n",
                          manual_target[0], manual_target[1]);
        } else if (c == 'd') {
            twin_log = !twin_log;
            Serial.printf("twin log %s (50 Hz 'T w x y z q1 q2')\n",
                          twin_log ? "on" : "off");
        } else if (c == 'l') {
            fast_log = true;
            fast_log_until = millis() + 3000;
            Serial.println("fast log 3 s");
        } else if (c == 'v') {
            float s[2];
            servo::get_signs(s);
            servo::set_signs(-s[0], s[1]);
            Serial.printf("shoulder sign = %+.0f (elbow %+.0f); re-send g/a\n", -s[0], s[1]);
        } else if (c == 'b') {
            float s[2];
            servo::get_signs(s);
            servo::set_signs(s[0], -s[1]);
            Serial.printf("elbow sign = %+.0f (shoulder %+.0f); re-send g/a\n", s[0], -s[1]);
        } else if (c == 'h') {
            home_enable = !home_enable;
            stand_state = 0;
            stand_hold = 0;
            Serial.printf("stand homing %s\n", home_enable ? "on" : "off");
        } else if (c == 'i') {
            g_imu_sign[0] = -g_imu_sign[0];
            Serial.printf("IMU X sign = %+.0f; send c to recalibrate gyro\n", g_imu_sign[0]);
        } else if (c == 'j') {
            g_imu_sign[1] = -g_imu_sign[1];
            Serial.printf("IMU Y sign = %+.0f; send c to recalibrate gyro\n", g_imu_sign[1]);
        } else if (c == 'o' || c == 'p') {
            // Shoulder PWM zero trim (re-indexed horn): shift 10 us per press.
            float us = servo::get_center_us(0) + ((c == 'o') ? 10.0f : -10.0f);
            servo::set_center_us(0, us);
            Serial.printf("shoulder center = %.0f us\n", servo::get_center_us(0));
        } else if (c == 'k') {
            Serial.printf("centers: shoulder %.0f us, elbow %.0f us\n",
                          servo::get_center_us(0), servo::get_center_us(1));
        } else if (c == 'c') {
            bool was_running = running;
            running = false;
            Serial.println("calibrating gyro: keep still");
            calibrate_gyro();
            running = was_running;
            if (running) next_ctrl_us = micros() + CTRL_PERIOD_US;
            Serial.println(running ? "calibration done; running" : "calibration done; hold");
        } else if (c == 't') {
            bool was_running = running;
            running = false;
            servo::self_test();
            delay(200);
            float q[2], qd[2];
            if (servo::has_feedback() && servo::read(q, qd)) {
                cmd[0] = q[0];
                cmd[1] = q[1];
            } else {
                cmd[0] = cmd[1] = 0.0f;
            }
            qdot_cmd[0] = qdot_cmd[1] = 0.0f;
            running = was_running;
            if (running) next_ctrl_us = micros() + CTRL_PERIOD_US;
            Serial.println(running ? "self-test done; running" : "self-test done; hold");
        }
    }
}

static void fail_blink(const char *msg) {
    Serial.println(msg);
    while (true) {
        digitalWrite(PIN_LED, HIGH);
        delay(100);
        digitalWrite(PIN_LED, LOW);
        delay(100);
    }
}

// ----------------------------------------------------------------------- main
void setup() {
    Serial.begin(SERIAL_BAUD);
    pinMode(PIN_LED, OUTPUT);
    delay(200);

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(IMU_I2C_HZ);
    Wire.setTimeOut(50);   // never block forever on a wedged I2C bus

    Serial.printf("waiting for IMU startup %d ms...\n", IMU_STARTUP_MS);
    delay(IMU_STARTUP_MS);

    // IMU first so the version/gyro check is visible even when the servo
    // rail is still off (the SCS backend fails to init without servo power).
    if (!imu_init()) fail_blink("IMU not found; check wiring/address 0x23");
    Serial.println("Calibrating gyro: keep the robot still");
    if (!calibrate_gyro()) fail_blink("gyro calibration failed");

    uint32_t t0 = millis();
    while (millis() - t0 < 1500) {
        int16_t raw[6];
        if (imu_read_raw(raw)) {
            float acc[3], gyro[3];
            raw_to_si(raw, acc, gyro);
            mahony_update(gyro, acc, 0.002f);
        }
        delay(2);
    }

    float q0[2];
    if (!servo::begin(q0)) fail_blink("servo init failed; check power/ID/wiring");
    for (int i = 0; i < 2; ++i) {
        cmd[i] = q0[i];
        q_obs[i] = q0[i];
        qd_obs[i] = 0.0f;
        qdot_cmd[i] = 0.0f;
    }
    Serial.printf("servo start q: %.2f %.2f rad\n", q0[0], q0[1]);

    last_imu_ok_ms = millis();
    next_ctrl_us = micros() + CTRL_PERIOD_US;
    // Stay in hold until the operator sends 'g'; bring-up checks (t, up, q)
    // must not happen while the policy is already driving the arm.
    running = false;
    Serial.println("ready; send g to run");
    // Task watchdog: a wedged loop (seen on the bench as a fully silent board)
    // reboots the chip; autorun resumes the app after boot.
    {
        esp_task_wdt_config_t twdt = {
            .timeout_ms = 8000,
            .idle_core_mask = 0,
            .trigger_panic = true,
        };
        if (esp_task_wdt_init(&twdt) != ESP_OK) {
            esp_task_wdt_reconfigure(&twdt);
        }
        esp_task_wdt_add(NULL);
    }
#if WIFI_TELEMETRY && WIFI_AP_DEFAULT_ON
    wifi_begin();
#endif
#if AUTORUN_ON_BOOT
    // Standalone mode: run straight away; the fall gate arms the policy only
    // once the robot is actually down and at rest.
    manual = false;
    auto_mode = false;
    policy_armed = false;
    fall_ticks = 0;
    running = true;
    Serial.println("autorun on: get-up waits for a fall");
    {
        const esp_partition_t *q = snap_partition();
        SnapHdr h = {0, 0, 0};
        if (q) esp_partition_read(q, 0, &h, sizeof h);
        if (h.magic == SNAP_MAGIC && h.len <= SR_LOG_RING_BYTES) {
            Serial.printf("saved get-up log: %lu bytes (send P to dump)\n",
                          (unsigned long)h.len);
        }
    }
#endif
}

void loop() {
    esp_task_wdt_reset();
    uint32_t now = micros();
    static uint32_t last_imu_us = 0;
    static uint32_t last_imu_ok_us = 0;

    // Read the IMU at a fixed 100 Hz. Reading it every loop iteration starves
    // the module: most I2C transactions fail and the attitude freezes.
    if ((int32_t)(now - last_imu_us) >= 10000) {
        last_imu_us = now;
        int16_t raw[6];
        if (imu_read_raw(raw)) {
            // Stuck-sensor guard: identical raw registers for 0.3 s mean the
            // I2C link is returning stale data (seen on the bench as frozen
            // telemetry). Escalate: re-init the IMU, then reset the bus.
            static int16_t prev_raw[6] = {0};
            static uint16_t same_raw = 0;
            static uint8_t recoveries = 0;
            if (memcmp(raw, prev_raw, sizeof(raw)) == 0) {
                if (++same_raw >= 30) {
                    same_raw = 0;
                    ++recoveries;
                    memset(prev_raw, 0, sizeof(prev_raw));
                    if (recoveries == 1) {
                        Serial.println("IMU stuck -> re-init");
                        imu_init();
                    } else if (recoveries == 2) {
                        Serial.println("IMU stuck -> bus reset");
                        imu_bus_reset();
                        imu_init();
                    } else {
                        Serial.println("IMU stuck -> hard bus reset");
                        imu_bus_reset();
                        delay(50);
                        imu_init();
                        recoveries = 0;
                    }
                }
            } else {
                same_raw = 0;
                recoveries = 0;
                memcpy(prev_raw, raw, sizeof(raw));
            }
            float acc[3], gyro[3];
            raw_to_si(raw, acc, gyro);
            for (int i = 0; i < 6; ++i) g_raw[i] = raw[i];
            g_gyro[0] = gyro[0];
            g_gyro[1] = gyro[1];
            g_gyro[2] = gyro[2];
            float dt = (last_imu_ok_us == 0)
                           ? 0.01f
                           : (now - last_imu_ok_us) * 1e-6f;
            last_imu_ok_us = now;
            dt = clampf(dt, 0.001f, 0.05f);
            mahony_update(gyro, acc, dt);
            last_imu_ok_ms = millis();
        }
    }

    bool imu_ok = (millis() - last_imu_ok_ms) < 100;
    if ((running || manual || auto_mode) && imu_ok && (int32_t)(now - next_ctrl_us) >= 0) {
        next_ctrl_us += CTRL_PERIOD_US;
        if ((int32_t)(now - next_ctrl_us) > (int32_t)CTRL_PERIOD_US) {
            next_ctrl_us = now + CTRL_PERIOD_US;
        }
        if (manual) {
            manual_step();
        } else {
            control_step();
        }
    } else if (!imu_ok) {
        servo::stop();
        // IMU lost mid-run: bring the bus and chip back instead of freezing.
        static uint32_t last_imu_recover = 0;
        if ((int32_t)(now - last_imu_recover) >= 1000000) {  // once per second
            last_imu_recover = now;
            Serial.println("IMU lost -> bus reset + re-init");
            imu_bus_reset();
            if (imu_init()) {
                last_imu_ok_ms = millis();
                Serial.println("IMU recovered");
            }
        }
    }

    handle_serial();

    static uint32_t last_telem_ms = 0;
    if (millis() - last_telem_ms > 250) {
        last_telem_ms = millis();
        float u[3];
        up_body(u);
        Serial.printf("up %+.2f %+.2f %+.2f | w %+5.1f %+5.1f %+5.1f | q %+.2f %+.2f | qd %+5.1f %+5.1f | %s\n",
                      u[0], u[1], u[2], g_gyro[0], g_gyro[1], g_gyro[2],
                      q_obs[0], q_obs[1], qd_obs[0], qd_obs[1],
                      manual ? "manual" : auto_mode ? "auto" : (running && imu_ok ? "run" : "hold"));
    }

    static uint32_t last_fast_us = 0;
    if (fast_log) {
        if ((int32_t)(millis() - fast_log_until) >= 0) {
            fast_log = false;
            Serial.println("fast log done");
        } else if ((int32_t)(now - last_fast_us) >= (int32_t)CTRL_PERIOD_US) {
            last_fast_us = now;
            float u[3];
            up_body(u);
            Serial.printf("F %+.2f %+.2f %+.2f | %+.2f %+.2f %+.2f | %+.3f %+.3f | %d | "
                          "%d %d %d %d %d %d\n",
                          u[0], u[1], u[2], g_gyro[0], g_gyro[1], g_gyro[2],
                          cmd[0], cmd[1], stand_state,
                          g_raw[0], g_raw[1], g_raw[2], g_raw[3], g_raw[4], g_raw[5]);
        }
    }

    static uint32_t last_twin_us = 0;
    if (twin_log && (int32_t)(now - last_twin_us) >= (int32_t)CTRL_PERIOD_US) {
        last_twin_us = now;
        // MuJoCo live-twin stream: raw IMU-frame attitude quat (w x y z) +
        // commanded joint angles. The PC tool (tools/live_twin.py) applies
        // the IMU_YAW90 body-frame mapping and drives the sim model.
        Serial.printf("T %+.3f %+.3f %+.3f %+.3f %+.2f %+.2f\n",
                      q_att[0], q_att[1], q_att[2], q_att[3],
                      q_obs[0], q_obs[1]);
    }

#ifdef ROBOT_SCS0009
    static uint32_t last_check_ms = 0;
    if (millis() - last_check_ms > 1000) {
        last_check_ms = millis();
        for (int i = 0; i < 2; ++i) {
            int v = servo::voltage_raw(i);
            int t = servo::temperature_c(i);
            if (v >= 0 && v < SERVO_VOLTAGE_MIN_RAW) {
                running = false;
                Serial.printf("servo %d low voltage: %.1f V; stopped\n", i, v / 10.0f);
            }
            if (t > SERVO_TEMP_LIMIT_C) {
                running = false;
                Serial.printf("servo %d over temperature: %d C; stopped\n", i, t);
            }
        }
    }
#endif

    static uint32_t last_led_ms = 0;
    if (millis() - last_led_ms > 250) {
        last_led_ms = millis();
        digitalWrite(PIN_LED, !digitalRead(PIN_LED));
    }
}
