---
title: 01 Nozioni di base
description: Principio di funzionamento, specifiche e BOM di SR-Support.
---

# 01 Nozioni di base

## 1.1 Principio di funzionamento

SR-Support è un dispositivo auto-raddrizzante attivo a 2-DOF (spalla + gomito):

- **Meccanismo**: un braccio a due giunti montato su una base quadrata; la spalla ruota attorno
  all'asse longitudinale del corpo e il gomito piega l'avambraccio;
- **Sensori**: un'IMU a 6 assi fornisce il quaternione di assetto; il firmware classifica ogni
  caduta in una delle quattro pose (`pitch_pos/neg`, `roll_pos/neg`, vedi
  [pagina 06](./06-debug-and-calibrate.md) 6.5) a partire dal vettore up nel sistema di
  riferimento del corpo;
- **Azionamento**: un esecutore di sequenze di riferimento - ogni posa ha una sequenza di
  waypoint (20 tick per waypoint, velocità di variazione 0.08 rad/tick) che pianta/fa leva con
  il braccio per far rotolare il corpo di nuovo in posizione eretta; `roll_neg` usa inoltre
  pompaggi a cuneo del gomito e un fallback a colpo di frusta;
- **Ripieghi**: timeout di 14 s, ri-pianificazione della posa e nuovo tentativo automatico dopo
  la soglia di caduta; `roll_neg` usa mantenimenti adattivi per stadio ed esce in ritrazione
  appena è in posizione eretta;
- **Verificato**: le quattro direzioni si rialzano direttamente in circa 1–6 s; lo stesso
  modello guida la simulazione MuJoCo e il gemello digitale in tempo reale dell'hardware
  ([pagina 08](./08-wifi-twin.md)).

## 1.2 Panoramica

| Voce | Specifica |
|---|---|
| Base | ~88 × 82 mm, 68 mm di altezza (piastra inferiore + supporto del servomotore di spalla, stampati in 3D) |
| Braccio | Asse della spalla 56 mm sopra la base, gomito 40.1 mm sopra la spalla; montante dell'avambraccio ~17 cm (tubo da 12 mm) |
| Massa | ~133 g (tabella delle masse del modello: foot 92.1 / arm1 20.7 / arm2 20.1 g, entrambi i servomotori inclusi) |
| Spalla | PTK7452MG; limiti manuali `[-1.85, +1.82]` rad (campo del giunto nella simulazione `[-1.07, +2.07]`) |
| Gomito | PTK7452MG; limiti manuali `[-0.90, +0.70]` rad (meccanici ~±1.55 rad) |
| Controllore | ESP32-S3-DevKitC-1 (framework Arduino / PlatformIO) |
| Assetto | IMU a 6 assi Juxi ICM42670P (indirizzo I²C 0x23, 100 kHz) |
| Pilotaggio servomotori | LEDC dell'ESP32, 50 Hz, 14 bit, larghezza d'impulso 500–2500 µs |

## 1.3 BOM

| Categoria | Componente | Q.tà | Note |
|---|---|---|---|
| Struttura | Stampati in 3D: piastra inferiore, supporto del servomotore di spalla, supporto del servomotore di gomito, montante superiore | 1 ciascuno | PETG o PLA, 15% di riempimento; le squadrette sono quelle fornite con i servomotori |
| Azionamento | Servomotore PTK7452MG 180° PWM | 2 | Ingranaggi in metallo, 25T, ~12.2 g, ~3.4 kg·cm a 6 V |
| Controllore | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Sensore | Modulo IMU Juxi ICM42670P | 1 | Alimentazione 3.3 V |
| Adattatore | Scheda adattatrice passiva per servomotori | 1 | GPIO → connettori a 3 pin, V+/GND in comune, senza PCA9685 |
| Cablaggio | Cavo dati USB-C, fili Dupont, prolunghe per servomotori | diversi | — |
| Alimentazione | Alimentatore per servomotori 5 V / ≥5 A | 1 | Un unico alimentatore 5 V alimenta l'ESP32 e i servomotori tramite un cavo a 1→2 (massa comune); **verificato per tutte e quattro le direzioni di rialzata** |

---

[← Torna all'indice del tutorial](./index.md)
