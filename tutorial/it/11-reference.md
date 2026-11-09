---
title: 11 Riferimenti: modello, parametri e licenze
description: File di riferimento del modello (MuJoCo XML / STL), parametri del firmware, le quattro sequenze di riferimento, stato verificato e licenze.
---

# 11 Riferimenti: modello, parametri e licenze

## 11.1 File di riferimento del modello

La simulazione usa MuJoCo MJCF (`.xml` + mesh `.stl`), condividendo il design dell'hardware stesso:

| File | Descrizione |
|---|---|
| `hardware/v1/robot_v1.xml` | Modello principale (geometria/masse allineate all'hardware) |
| `hardware/v1/meshes/*.stl` | 6 mesh STL che si compongono in 4 gruppi stampati (piastra/guscio della base, supporto della spalla, staffa del braccio superiore/supporto del gomito, avambraccio) |
| `hardware/v1/meshes/print_mass_model.json` | Tabella delle masse stampate per parte (15% di riempimento) |

Nessun URDF è incluso; per l'uso con ROS, esportane uno dal CAD/dalle mesh qui sopra.

## 11.2 Parametri del firmware (`firmware/sr_support_b_ptk/include/config.h`)

| Parametro | Valore | Significato |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | Periodo di controllo a 50 Hz |
| `MAX_CMD_RATE` | 0.08 rad/tick | Limite di velocità di variazione dell'uscita (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Soglia up_z della soglia di caduta |
| `FALL_W_QUIET` | 0.9 rad/s | Soglia di velocità angolare della soglia di caduta |
| `FALL_CONFIRM_TICKS` | 25 | Conferma della soglia di caduta (0.5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Tick per waypoint di riferimento |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Velocità di ritrazione |
| `EXEC_DONE_TICKS` | 50 | Tick consecutivi in piedi per completare |
| `EXEC_TIMEOUT_MS` | 14000 | Timeout per sequenza di riferimento |
| `EXEC_COOLDOWN_TICKS` | 75 | Cooldown dopo completamento/timeout (1.5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Tick di conferma del cambio di posa |
| `EXEC_SWITCH_UP` | 0.60 | up_z massimo per un cambio |
| `EXEC_SWITCH_W` | 0.8 rad/s | Velocità angolare massima per un cambio |
| `EXEC_MIN_SWITCH_AGE` | 25 | Tick minimo per un cambio |
| `EXEC_MAX_SWITCHES` | 5 | Cambi massimi per esecuzione |
| `EXEC_NEUTRAL_MAX` | 120 | Tick massimi di ritrazione in neutro |
| `SERVO_SHOULDER_CENTER_US` | 1681 | Impulso di zero della spalla (valore del centro visivo memorizzato 2026-11; riazzera secondo la [pagina 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Impulso di zero del gomito (idem) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Limiti dei comandi manuali della spalla |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Campo manuale (l'esecutore usa ±1.55 meccanici) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Direzione dei servomotori |
| `IMU_YAW90` | 1 | IMU montata ruotata di 90° |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Filtro di assetto: guadagno di correzione dell'accelerometro / banda di fiducia |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Hotspot (`w` lo attiva/disattiva; attivo all'avvio) |

## 11.3 Sequenze di riferimento (spalla, gomito; rad; identiche valore per valore a `training/b_line/getup_reference_b39.py`)

| Posa | Sequenza |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` pressione diretta a velocità piena (mantenimento ≤40 tick) → pompaggi a cuneo `[-1.80,0.35] → [-1.80,0.05]` ×2 (ciascuno ≤30) → fallback: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (colpo di frusta, mantenimento ≤40) → mantenimento finale ≤90 → ritrazione |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 11.4 Stato verificato e ispezione di fabbrica (2026-11-06)

- **Ispezione di fabbrica**: ogni unità finita riceve: zeri dei servomotori definiti e memorizzati
  per unità ([pagina 05](./05-zero-tool.md)), calibrazione di zero di giroscopio + accelerometro
  (NVS) e un test di rialzata nelle quattro direzioni prima della spedizione;
- tutte e quattro le direzioni verificate sul robot reale, ciascuna come **rialzata diretta**
  (senza ribaltamento), circa 1–6 s; nessuna violazione dell'inviluppo dei servomotori;
- ricetta finale di `roll_neg`: pressione diretta a corsa completa + pompaggi a cuneo del gomito
  ×2, nuovo tentativo a colpo di frusta come fallback (lo schema precedente con ribaltamento +
  ri-pianificazione è ritirato);
- la pipeline di assetto è stata corretta con la calibrazione del bias dell'accelerometro (vedi
  [pagina 06, 6.2](./06-debug-and-calibrate.md)); le pose sdraiate ora corrispondono al robot reale;
- `roll_neg` non si riproduce ancora nel modello di simulazione a massa 1× (massa/attrito del
  braccio diversi); è una lacuna nota del modello - il firmware per l'hardware è validato
  sull'hardware.

## 11.5 Licenze

- Firmware/codice di addestramento della linea B: MIT / Apache-2.0;
- CAD/STL della linea B: CERN-OHL-S-2.0 (reciprocità forte — verifica gli obblighi prima dell'uso commerciale);
- SelfRisingRobot: nessuna licenza; questo tutorial non contiene nulla del suo codice, dei suoi waypoint o dei suoi modelli;
- Brevetto CN109693729A/B: esegui una revisione FTO prima dell'uso commerciale.

---

[← Torna all'indice del tutorial](./index.md)
