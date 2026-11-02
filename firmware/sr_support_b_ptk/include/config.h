// Hardware configuration for the B-line (PTK7452MG PWM) build.
// Target board: ESP32-S3-DevKitC-1, Arduino framework (PlatformIO or Arduino IDE).
//
// Adapter board in this project:
//   - passive pass-through: ESP32 GPIO -> 3-pin servo headers
//   - shared servo V+/GND rail, cascadable headers
//   - no PCA9685 / no GPIO expander
//   => two direct 50 Hz LEDC PWM channels (GPIO4/5 in this example).
#pragma once

// This project is the B-line (PWM) build only. Defining ROBOT_PWM here also
// lets the .cpp/.ino compile in Arduino IDE, where no -D build flag is added.
#define ROBOT_PWM 1

// ---------------------------------------------------------------- pin mapping
// Adapter mapping (your board): CH1..CH8 = GPIO4,5,6,7,15,16,17,18.
// B-line uses CH1/CH2 for the two servos and repurposes CH3/CH4 signal pins
// for I2C. CH5..CH8 stay unused.
//
// IMPORTANT: the servo header V+ is the 6 V servo rail. Never power the IMU
// from it. IMU VCC goes to ESP32 3V3; IMU GND can use a CH3/CH4 header GND.
#define PIN_I2C_SDA 6
#define PIN_I2C_SCL 7
#define PIN_LED 2

// --------------------------------------------------- Juxi ICM42670P IMU module
// Juxi high-precision IMU carrier (ICM42670P). I2C address 0x23, 100 kHz.
// Registers 0x04..0x0F hold little-endian int16 accel (g, +/-16 g) and gyro
// (dps, +/-2000 dps). Mount +X forward, +Y left, +Z up; if not, edit the axis
// mapping in main.cpp (search "IMU AXES").
#define IMU_I2C_ADDR 0x23
#define IMU_I2C_HZ 100000
// Some Juxi modules need a few seconds after power-up before I2C is reliable.
// The old internal wiki says 5 s; keep this conservative for first bring-up.
#define IMU_STARTUP_MS 5000

// ------------------------------------------------- policy / control constants
#define POLICY_DT 0.02f
#define CTRL_PERIOD_US 20000
#define MAX_CMD_RATE 0.08f   // rad per 20 ms control step (4 rad/s)
#define POLICY_ACTION_DELTA 0.08f  // SR-style increment action (rad/step)
#define ACT_FILTER_ALPHA 1.0f  // policy action low-pass (1.0 = off)

// ------------------------------------------------------------ IMU mount frame
// The IMU is mounted rotated +90 deg about the body vertical relative to the
// arm frame (verified 2026-10-26 by tilting the upright robot toward / away
// from the arm side). The model convention is x forward, y left, z up, with
// the shoulder rotating about x; convert the IMU-frame up vector into it:
//   up_body = (up_imu.y, -up_imu.x, up_imu.z)
#define IMU_YAW90 1

// ------------------------------------------------------------- attitude filter
#define MAHONY_KP 6.0f
#define MAHONY_KI 0.02f
#define ACCEL_TRUST_BAND 2.5f     // m/s^2; ignore accel during hard impacts

#define SERIAL_BAUD 115200
// Run without sending 'g': the fall gate arms the policy once the robot is
// down and at rest, and the stand logic disarms it again.
#define AUTORUN_ON_BOOT 1
#define GRAVITY 9.80665f

// ================================================= PTK7452MG (PWM, B-line) ====
// PTK7452MG: 180 deg PWM, metal gear, 23.6 x 26.9 x 11.7 mm, ~12.2 g, 25T,
// 4.8-7.4 V. Official torque 2.8/3.4/4.5 kg*cm at 4.8/6/7.4 V.
// For a first B-line build use 6 V / >=5 A and expect ~3.4 kg*cm; at 7.4 V it
// reaches ~4.5 kg*cm (same as the reference PTK7465MG) but check heat/current.
// Center is 1520 us on many PTK batches; 500-2500 us spans about 180 deg.
#define SERVO_FREQ_HZ 50
// ESP32-S3 LEDC max resolution is 14 bits (CONFIG_SOC_LEDC_TIMER_BIT_WIDTH=14).
// 14 bits at 50 Hz gives ~1.22 us per count; 16-bit makes ledcAttach() fail.
#define SERVO_RES_BITS 14
#define PIN_SERVO_SHOULDER 4
#define PIN_SERVO_ELBOW 5
#define Q_HALF_RANGE 1.55f
// B-line 39 mm build: the shoulder horn is re-indexed ~29 deg (2 teeth on the
// 25T spline), so the usable window is asymmetric. These are the command
// limits the policy and scripted routine use (mirrors the b39h26ri_sr5 sim
// spec). Mechanical travel is a little wider on the short side.
#define Q_SHOULDER_MIN (-1.07f)
#define Q_SHOULDER_MAX (2.07f)
#define Q_ELBOW_MIN (-0.80f)
#define Q_ELBOW_MAX (0.80f)

// ------------------------------------------------- scripted stand routine
// (legacy; replaced by the deterministic get-up executor below)
#define PUSH_TARGET 1.9f       // shoulder push target, rad (7.4V overshoots at 2.0)
#define PUSH_RATE 0.04f        // rad per control tick while pushing
#define PUSH_ELBOW 0.9f        // elbow target during push/hold (manual demo pair)
#define PUSH_ELBOW_RATE 0.08f  // elbow leads the shoulder so the arm clears the floor
#define PUSH_HOLD_TICKS 20     // hold before the lift-out
#define PULL_RATE 0.01f        // rad per tick while lifting out (0.5 rad/s)

// ------------------------------------------- reference + feedback get-up
// Mirrors training/b_line/getup_executor.py: 20 control ticks (0.4 s) per
// reference waypoint; the final phase retracts the arm to neutral at
// EXEC_RETRACT_RATE. If the body settles on another lying axis (e.g. the
// roll-pose yaw conversion turning the body onto the pitch axis), the
// executor retracts to neutral and re-plans to the reference of the new
// pose instead of running the wrong sequence to the timeout.
#define EXEC_STEPS_PER_WP 20
#define EXEC_RETRACT_RATE 0.033f
#define EXEC_DONE_TICKS 50
#define EXEC_TIMEOUT_MS 14000
#define EXEC_COOLDOWN_TICKS 75

// ---- offline telemetry: RAM ring buffer, dumped over serial with 'L' ----
#define SR_LOG_RING_BYTES 131072   // ~40 s of 50 Hz state lines
// ---- WiFi AP live telemetry: TCP 3333, 'w' toggles, on by default ----
#define WIFI_TELEMETRY 1
#define WIFI_AP_SSID "SR-Support"
#define WIFI_AP_PASS "srsupport"
#define WIFI_AP_DEFAULT_ON 1

#define EXEC_SWITCH_TICKS 15      // settled on another axis for 0.3 s -> re-plan
#define EXEC_SWITCH_UP 0.60f      // re-plan only while the body is still low
#define EXEC_SWITCH_W 0.8f        // rad/s; re-plan only when the body is at rest
#define EXEC_MIN_SWITCH_AGE 25    // ticks after a reference start (0.5 s)
#define EXEC_MAX_SWITCHES 5
#define EXEC_NEUTRAL_MAX 120      // cap on the neutral retract phase
// The fall gate waits for a fully fallen, genuinely quiet robot; the old
// 0.2 s / 1.5 rad/s window armed mid-tumble and misclassified the pose.
#define FALL_UP_Z 0.30f
#define FALL_W_QUIET 0.9f
#define FALL_CONFIRM_TICKS 25
#define PULL_PAUSE_UP 0.97f    // stop lifting while the body sags below this
#define ROUTINE_UP_MIN 0.60f   // body-up trigger with the arm still out
#define ROUTINE_UP_FALL 0.50f  // abort below this
#define ROUTINE_ARM_OUT 0.50f  // |shoulder| above this = arm still out
#define ROUTINE_QUIET_STEPS 20
#define LEFT_UP_LO 0.35f       // left-side wedge window (short-travel side)
#define LEFT_UP_HI 0.75f
#define LEFT_FLAT_UP 0.35f     // flat-lying pump window: LEFT_FLAT_LO < up_z < this
#define LEFT_FLAT_LO (-0.2f)   // inverted poses (below) are left to the policy
#define PUMP_AMP 0.4f          // unused; the pump sweeps the full elbow range
#define PUMP_PERIOD_TICKS 20   // 0.4 s at 50 Hz
#define PUMP_MAX_TICKS 400     // flat-lying square pump budget
#define PUMP_INVERT_UP (-0.45f)  // a settled inverted pose is not the pump working
#define PUMP_INVERT_TICKS 20     // stop after 0.4 s inverted and hand to the policy
#define PUMP_WEDGE_HI 0.8f     // wedge cosine pump: elbow centre
#define PUMP_WEDGE_TICKS 120
// Direction confirmed on hardware 2026-10-22: shoulder +q moves the big arm
// toward -Y, elbow +q moves the forearm toward +X (same as the sim joints).
#define SERVO_SHOULDER_SIGN -1.0f
#define SERVO_ELBOW_SIGN -1.0f
#define SERVO_CENTER_US 1520.0f
// Shoulder zero after the horn re-index (2 teeth, ~29 deg): the vertical arm
// sits 320 us above the servo's electrical centre, leaving ~119 deg of travel
// toward the get-up side (us down to 500) and ~60 deg the other way.
#define SERVO_SHOULDER_CENTER_US 1840.0f
#define SERVO_US_PER_RAD 636.62f  // 2000 us / pi
#define SERVO_MIN_US 500
#define SERVO_MAX_US 2500
#define JOINT_FEEDBACK 0
