// Servo backend interface: SCS bus servos (feedback) or PTK/PWM (no feedback).
#pragma once

namespace servo {

// Initialize the servo hardware. On success, q_init is filled with the joint
// angles corresponding to the current physical pose (measured for SCS,
// neutral for PWM).
bool begin(float q_init[2]);

// True when the backend can report measured joint angles.
bool has_feedback();

// Read measured joint angles and velocities. Only valid when has_feedback().
bool read(float q[2], float qd[2]);

// Command joint angles (radians, model convention).
void write(const float q[2]);

// Hold the current command.
void stop();

// Emergency release: detach PWM (servo loses torque). B-line has no position
// feedback, so after release the arm may fall; cut servo power for a full stop.
void release();

// Slow sweep for wiring/sign verification.
void self_test();

// Runtime direction calibration (model q -> servo rotation). Defaults come
// from SERVO_SHOULDER_SIGN / SERVO_ELBOW_SIGN; the 'v'/'b' serial commands
// flip them so the correct mapping can be found without reflashing.
void set_signs(float shoulder, float elbow);
void get_signs(float out[2]);

// Runtime zero calibration: PWM microseconds that correspond to q = 0.
// After re-indexing the shoulder horn (~29 deg) the vertical pose is no
// longer at SERVO_CENTER_US; the 'o'/'p' serial commands nudge this live.
void set_center_us(int i, float us);
float get_center_us(int i);

#ifdef ROBOT_SCS0009
// Latest voltage/temperature, raw register units; -1 if unavailable.
int voltage_raw(int i);
int temperature_c(int i);
#endif

}  // namespace servo
