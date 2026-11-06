---
title: 10 Referenz: Modell, Parameter und Lizenzierung
description: Referenzmodelldateien (MuJoCo XML / STL), Firmware-Parameter, die vier Referenzsequenzen, verifizierter Stand und Lizenzierung.
---

# 10 Referenz: Modell, Parameter und Lizenzierung

## 10.1 Referenzmodelldateien

Die Simulation verwendet MuJoCo MJCF (`.xml` + `.stl`-Meshes) und teilt das Design der Hardware:

| Datei | Beschreibung |
|---|---|
| `hardware/v1/robot_v1.xml` | Hauptmodell (Geometrie/Masse an die Hardware angepasst) |
| `hardware/v1/meshes/*.stl` | 6 STL-Meshes, die sich zu 4 gedruckten Gruppen zusammensetzen (Grundplatte/Gehäuse, Schulterhalterung, Oberarmhalterung/Ellenbogenhalterung, Unterarm) |
| `hardware/v1/meshes/print_mass_model.json` | Gedruckte Massentabelle pro Teil (15 % Infill) |

Es ist keine URDF enthalten; für die ROS-Nutzung exportieren Sie eine aus dem CAD/den Meshes oben.

## 10.2 Firmware-Parameter (`firmware/sr_support_b_ptk/include/config.h`)

| Parameter | Wert | Bedeutung |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | 50-Hz-Regelperiode |
| `MAX_CMD_RATE` | 0.08 rad/tick | Stellratenbegrenzung des Ausgangs (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Up_z-Schwelle des Fall-Gates |
| `FALL_W_QUIET` | 0.9 rad/s | Winkelgeschwindigkeits-Schwelle des Fall-Gates |
| `FALL_CONFIRM_TICKS` | 25 | Bestätigung des Fall-Gates (0,5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Ticks pro Referenzwegpunkt |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Einfahrrate |
| `EXEC_DONE_TICKS` | 50 | Aufeinanderfolgende Steh-Ticks bis zum Abschluss |
| `EXEC_TIMEOUT_MS` | 14000 | Timeout pro Referenz |
| `EXEC_COOLDOWN_TICKS` | 75 | Abklingzeit nach done/Timeout (1,5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Bestätigungs-Ticks für Posenumschaltung |
| `EXEC_SWITCH_UP` | 0.60 | Maximales up_z für eine Umschaltung |
| `EXEC_SWITCH_W` | 0.8 rad/s | Maximale Winkelgeschwindigkeit für eine Umschaltung |
| `EXEC_MIN_SWITCH_AGE` | 25 | Frühester Tick für eine Umschaltung |
| `EXEC_MAX_SWITCHES` | 5 | Maximale Umschaltungen pro Lauf |
| `EXEC_NEUTRAL_MAX` | 120 | Maximale Neutral-Einfahr-Ticks |
| `SERVO_SHOULDER_CENTER_US` | 1681 | Nullpunkt-Puls der Schulter (Wert der visuellen Mitte, eingebrannt 2026-11; neu nullen gemäß [Seite 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Nullpunkt-Puls des Ellenbogens (dito) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Manuelle Befehlgrenzen der Schulter |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Manueller Bereich (der Ausführer nutzt mechanisch ±1,55) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Servorichtung |
| `IMU_YAW90` | 1 | IMU um 90° gedreht montiert |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Lagefilter: Beschleunigungs-Korrekturverstärkung / Vertrauensband |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Hotspot (`w` schaltet ihn um; beim Booten an) |

## 10.3 Referenzsequenzen (Schulter, Ellenbogen; rad; wertgleich mit `training/b_line/getup_reference_b39.py`)

| Pose | Sequenz |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` direkter Druck mit voller Geschwindigkeit (Halten ≤40 Ticks) → Keilpumpen `[-1.80,0.35] → [-1.80,0.05]` ×2 (je Halten ≤30) → Fallback: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (Whip-Slam, Halten ≤40) → finales Halten ≤90 → einfahren |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 10.4 Verifizierter Stand und Werksprüfung (2026-11-06)

- **Werksprüfung**: Jedes fertige Gerät erhält – pro Gerät definierte und eingebrannte
  Servo-Nullpunkte ([Seite 05](./05-zero-tool.md)), Gyro- + Beschleunigungs-Nullpunkt-Kalibrierung
  (NVS) und einen Aufrichtest in vier Richtungen vor dem Versand;
- Alle vier Richtungen wurden am realen Roboter verifiziert, jeweils als **direktes Aufstehen**
  (kein Überrollen), etwa 1–6 s; keine Verletzungen der Servo-Grenzwerte;
- Endgültiges `roll_neg`-Rezept: direkter Druck über den vollen Verfahrweg + Ellenbogen-Keilpumpen
  ×2, Whip-Slam-Wiederholung als Fallback (das frühere Überroll- + Neuplanungs-Schema ist außer
  Betrieb);
- Die Lageverarbeitung wurde mit der Beschleunigungs-Bias-Kalibrierung korrigiert (siehe
  [Seite 06, 6.2](./06-debug-and-calibrate.md)); die Liegeposen stimmen jetzt mit dem realen
  Roboter überein;
- `roll_neg` lässt sich im Simulationsmodell mit 1×-Masse weiterhin nicht reproduzieren
  (Armmasse/Reibung weichen ab); das ist eine bekannte Modelllücke – die Hardware-Firmware wird
  auf der Hardware validiert.

## 10.5 Lizenzierung

- B-Line-Firmware/Trainingscode: MIT / Apache-2.0;
- B-Line-CAD/STL: CERN-OHL-S-2.0 (starke Reziprozität – prüfen Sie die Pflichten vor kommerzieller
  Nutzung);
- SelfRisingRobot: keine Lizenz; dieses Tutorial enthält keinen Code, keine Wegpunkte und keine
  Modelle davon;
- Patent CN109693729A/B: Führen Sie vor kommerzieller Nutzung eine FTO-Prüfung durch.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
