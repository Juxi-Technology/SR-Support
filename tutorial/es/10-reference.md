---
title: 10 Referencia: modelo, parámetros y licencias
description: Archivos de referencia del modelo (MuJoCo XML / STL), parámetros del firmware, las cuatro secuencias de referencia, estado verificado y licencias.
---

# 10 Referencia: modelo, parámetros y licencias

## 10.1 Archivos de referencia del modelo

La simulación usa MuJoCo MJCF (`.xml` + mallas `.stl`), compartiendo el diseño del propio hardware:

| Archivo | Descripción |
|---|---|
| `hardware/v1/robot_v1.xml` | Modelo principal (geometría/masa ajustadas al hardware) |
| `hardware/v1/meshes/*.stl` | 6 mallas STL que se ensamblan en 4 grupos impresos (placa/carcasa de la base, soporte del hombro, soporte del brazo superior/soporte del codo, antebrazo) |
| `hardware/v1/meshes/print_mass_model.json` | Tabla de masas impresas por pieza (15 % de relleno) |

No se incluye ningún URDF; para usar ROS, exporta uno desde el CAD/las mallas de arriba.

## 10.2 Parámetros del firmware (`firmware/sr_support_b_ptk/include/config.h`)

| Parámetro | Valor | Significado |
|---|---|---|
| `POLICY_DT` / `CTRL_PERIOD_US` | 0.02 s / 20000 µs | Periodo de control de 50 Hz |
| `MAX_CMD_RATE` | 0.08 rad/tick | Límite de giro de la salida (4 rad/s) |
| `FALL_UP_Z` | 0.30 | Umbral de up_z de la condición de caída |
| `FALL_W_QUIET` | 0.9 rad/s | Umbral de velocidad angular de la condición de caída |
| `FALL_CONFIRM_TICKS` | 25 | Confirmación de la condición de caída (0.5 s) |
| `EXEC_STEPS_PER_WP` | 20 | Ticks por punto de paso de referencia |
| `EXEC_RETRACT_RATE` | 0.033 rad/tick | Velocidad de retracción |
| `EXEC_DONE_TICKS` | 50 | Ticks consecutivos de pie para terminar |
| `EXEC_TIMEOUT_MS` | 14000 | Tiempo de espera por referencia |
| `EXEC_COOLDOWN_TICKS` | 75 | Enfriamiento tras completar o agotar el tiempo de espera (1.5 s) |
| `EXEC_SWITCH_TICKS` | 15 | Ticks de confirmación de cambio de postura |
| `EXEC_SWITCH_UP` | 0.60 | up_z máximo para un cambio |
| `EXEC_SWITCH_W` | 0.8 rad/s | Velocidad angular máxima para un cambio |
| `EXEC_MIN_SWITCH_AGE` | 25 | Tick más temprano para un cambio |
| `EXEC_MAX_SWITCHES` | 5 | Cambios máximos por ejecución |
| `EXEC_NEUTRAL_MAX` | 120 | Ticks máximos de retracción al neutro |
| `SERVO_SHOULDER_CENTER_US` | 1681 | Pulso cero del hombro (valor de centro visual grabado en 2026-11; vuelve a poner a cero según la [página 05](./05-zero-tool.md)) |
| `SERVO_CENTER_US` | 1456 | Pulso cero del codo (ídem) |
| `SERVO_US_PER_RAD` | 636.62 | 2000 µs / π |
| `Q_SHOULDER_MIN/MAX` | −1.85 / +1.82 rad | Límites de los comandos manuales del hombro |
| `Q_ELBOW_MIN/MAX` | −0.90 / +0.70 rad | Rango manual (el ejecutor usa ±1.55 mecánicamente) |
| `SERVO_SHOULDER_SIGN/ELBOW_SIGN` | −1 / −1 | Dirección de los servos |
| `IMU_YAW90` | 1 | IMU montada con 90° de rotación |
| `MAHONY_KP` / `ACCEL_TRUST_BAND` | 6.0 / 2.5 m/s² | Filtro de actitud: ganancia de corrección del acelerómetro / banda de confianza |
| `WIFI_AP_SSID` / `WIFI_AP_PASS` | SR-Support / srsupport | Punto de acceso (`w` lo alterna; activo al arrancar) |

## 10.3 Secuencias de referencia (hombro, codo; rad; con valores idénticos a los de `training/b_line/getup_reference_b39.py`)

| Postura | Secuencia |
|---|---|
| `roll_pos` | `[1.75,-0.90] → [-0.25,-0.90] → retract` |
| `roll_neg` | `[-1.80,0.70]` presión directa a velocidad completa (espera ≤40 ticks) → bombeos de cuña `[-1.80,0.35] → [-1.80,0.05]` ×2 (cada espera ≤30) → respaldo: `[0.35,0.70] → [0.35,1.10] → [-1.80,0.05]` (latigazo, espera ≤40) → espera final ≤90 → retraer |
| `pitch_pos` | `[-1.32,1.45] → [-0.25,1.45] → retract` |
| `pitch_neg` | `[-1.32,-1.65] → [-0.25,-1.65] → retract` |

## 10.4 Estado verificado e inspección de fábrica (2026-11-06)

- **Inspección de fábrica**: cada unidad acabada recibe: ceros de servo definidos y grabados por
  unidad ([página 05](./05-zero-tool.md)), calibración de cero de giroscopio + acelerómetro
  (NVS), y una prueba de incorporación en las cuatro direcciones antes de enviarse;
- Las cuatro direcciones verificadas en el robot real, cada una como **incorporación directa**
  (sin volcar por encima), unos 1–6 s; sin violaciones de la envolvente de los servos;
- Receta final de `roll_neg`: presión directa a recorrido completo + bombeos de cuña de codo ×2,
  reintento de latigazo como respaldo (el esquema anterior de volcar por encima + replanificar
  queda retirado);
- La cadena de actitud se corrigió con la calibración de sesgo del acelerómetro (véase la
  [página 06, 6.2](./06-debug-and-calibrate.md)); las posturas tumbadas ahora coinciden con el
  robot real;
- `roll_neg` sigue sin reproducirse en el modelo de simulación de masa 1× (la masa y la fricción
  del brazo difieren); es una laguna conocida del modelo: el firmware del hardware se valida
  sobre el hardware.

## 10.5 Licencias

- Código de firmware/entrenamiento de la línea B: MIT / Apache-2.0;
- CAD/STL de la línea B: CERN-OHL-S-2.0 (reciprocidad fuerte: revisa las obligaciones antes de
  un uso comercial);
- SelfRisingRobot: sin licencia; este tutorial no contiene nada de su código, puntos de paso ni
  modelos;
- Patente CN109693729A/B: realiza una revisión FTO antes de un uso comercial.

---

[← Volver al índice del tutorial](./index.md)
