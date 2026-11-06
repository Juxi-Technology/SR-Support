// I2C scanner for the B-line IMU bring-up.
//
// Wiring (same as firmware/sr_support_b_ptk/include/config.h):
//   IMU VCC -> ESP32 3V3
//   IMU GND -> CH3/CH4 GND or ESP32 GND
//   IMU SDA -> CH3 signal (GPIO6)
//   IMU SCL -> CH4 signal (GPIO7)
//
// Build/upload:
//   pio run -d firmware/i2c_scanner -t upload --upload-port COMx
// Monitor (avoid auto-reset):
//   pio device monitor --rts 0 --dtr 0 -b 115200 -p COMx
//
// Expected for the Juxi 6-axis module: found 0x23.
// If you see 0x68/0x69, it is likely an MPU6050-class module, not this firmware.
// If nothing is found, check 3.3V, GND, SDA/SCL swap, and continuity from the
// CH3/CH4 signal pins to GPIO6/7. Never connect the IMU VCC to servo V+ (6V).

#include <Arduino.h>
#include <Wire.h>

#define SDA_PIN 6
#define SCL_PIN 7

void setup() {
  Serial.begin(115200);
  delay(1000);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  Serial.println();
  Serial.printf("I2C scanner: SDA=GPIO%d SCL=GPIO%d @100kHz\n", SDA_PIN, SCL_PIN);
  Serial.println("Expect Juxi IMU at 0x23.");
}

void loop() {
  uint8_t found = 0;
  Serial.println("scan...");
  for (uint8_t addr = 1; addr < 127; ++addr) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  found 0x%02X\n", addr);
      ++found;
    }
  }
  if (found == 0) {
    Serial.println("  no device; check 3V3/GND/SDA/SCL and CH3/CH4 mapping");
  }
  delay(2000);
}
