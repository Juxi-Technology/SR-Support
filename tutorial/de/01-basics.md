---
title: 01 Grundlagen
description: Funktionsprinzip, Spezifikationen und Stückliste des SR-Support.
---

# 01 Grundlagen

## 1.1 Funktionsprinzip

SR-Support ist ein aktives Selbstaufrichtungsgerät mit 2 DOF (Schulter + Ellenbogen):

- **Mechanik**: ein zweigelenkiger Arm auf einer quadratischen Basis; die Schulter schwenkt um die
  Längsachse des Körpers und der Ellenbogen klappt den Unterarm ein;
- **Sensorik**: eine 6-Achsen-IMU liefert das Lage-Quaternion; die Firmware ordnet jeden Sturz
  anhand des Hochvektors im Körperkoordinatensystem einer von vier Posen zu (`pitch_pos/neg`,
  `roll_pos/neg`, siehe [Seite 06](./06-debug-and-calibrate.md) 6.5);
- **Aktorik**: ein Referenzsequenz-Ausführer – jede Pose hat einen Wegpunktplan
  (20 Ticks pro Wegpunkt, 0,08 rad/Tick Stellrate), der den Arm aufsetzt/abhebelt, um den Körper
  wieder aufzurichten; `roll_neg` nutzt zusätzlich Keil-Pumpbewegungen mit dem Ellenbogen und
  einen Whip-Slam-Fallback;
- **Fallbacks**: 14-s-Timeout, Neuplanung der Pose und automatischer Wiederholungsversuch nach dem
  Fall-Gate; `roll_neg` verwendet stufenweise adaptive Haltezeiten und geht zum Einfahren über,
  sobald es aufrecht steht;
- **Verifiziert**: vier Richtungen stehen direkt in etwa 1–6 s auf; dasselbe Modell treibt die
  MuJoCo-Simulation und den Live-Zwilling der Hardware an ([Seite 08](./08-wifi-twin.md)).

## 1.2 Übersicht

| Element | Spezifikation |
|---|---|
| Basis | ~88 × 82 mm, 68 mm hoch (Grundplatte + Schulter-Servohalterung, 3D-gedruckt) |
| Arm | Schulterachse 56 mm über der Basis, Ellenbogen 40,1 mm über der Schulter; Unterarmstrebe ~17 cm (12-mm-Rohr) |
| Masse | ~133 g (Massentabelle des Modells: Fuß 92,1 / Arm1 20,7 / Arm2 20,1 g, inklusive beider Servos) |
| Schulter | PTK7452MG; manuelle Grenzen `[-1.85, +1.82]` rad (Gelenkbereich der Simulation `[-1.07, +2.07]`) |
| Ellenbogen | PTK7452MG; manuelle Grenzen `[-0.90, +0.70]` rad (mechanisch ~±1,55 rad) |
| Controller | ESP32-S3-DevKitC-1 (Arduino-Framework / PlatformIO) |
| Lageerfassung | Juxi ICM42670P 6-Achsen-IMU (I²C-Adresse 0x23, 100 kHz) |
| Servoansteuerung | ESP32 LEDC, 50 Hz, 14 Bit, 500–2500 µs Pulsweite |

## 1.3 Stückliste

| Kategorie | Teil | Menge | Hinweise |
|---|---|---|---|
| Struktur | 3D-gedruckt: Grundplatte, Schulter-Servohalterung, Ellenbogen-Servohalterung, obere Strebe | je 1 | PETG oder PLA, 15 % Infill; die Servohörner sind die mit den Servos mitgelieferten |
| Aktorik | PTK7452MG 180° PWM-Servo | 2 | Metallgetriebe, 25T, ~12,2 g, ~3,4 kg·cm bei 6 V |
| Controller | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Sensor | Juxi ICM42670P IMU-Modul | 1 | 3,3-V-Versorgung |
| Adapter | Passive Servo-Adapterplatine | 1 | GPIO → 3-polige Stiftleisten, gemeinsames V+/GND, kein PCA9685 |
| Verkabelung | USB-C-Datenkabel, Dupont-Kabel, Servoverlängerungen | mehrere | — |
| Stromversorgung | Servo-Netzteil 5 V / ≥5 A | 1 | Ein 5-V-Netzteil versorgt ESP32 und Servos über ein 1-auf-2-Kabel (gemeinsame Masse); **verifiziert für alle vier Aufrichtrichtungen** |

---

[← Zurück zum Tutorial-Inhalt](./index.md)
