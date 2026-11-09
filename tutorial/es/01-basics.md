---
title: 01 Conceptos básicos
description: Principio de funcionamiento, especificaciones y lista de materiales del SR-Support.
---

# 01 Conceptos básicos

## 1.1 Principio de funcionamiento

SR-Support es un dispositivo auto-enderezante activo de 2 GDL (hombro + codo):

- **Mecanismo**: un brazo de dos articulaciones montado sobre una base cuadrada; el hombro gira
  alrededor del eje longitudinal del cuerpo y el codo pliega el antebrazo;
- **Sensado**: una IMU de 6 ejes proporciona el cuaternión de actitud; el firmware clasifica cada
  caída en una de cuatro posturas (`pitch_pos/neg`, `roll_pos/neg`, véase la
  [página 06](./06-debug-and-calibrate.md) 6.5) a partir del vector «arriba» en el marco del cuerpo;
- **Accionamiento**: un ejecutor de secuencias de referencia; cada postura tiene una secuencia de
  puntos de paso (20 ticks por punto de paso, giro de 0.08 rad/tick) que apoya y apalanca el brazo
  para hacer rodar el cuerpo y volver a enderezarlo; `roll_neg` además usa bombeos de cuña de codo
  y un recurso de último momento de latigazo;
- **Mecanismos de respaldo**: tiempo de espera de 14 s, replanificación de postura y reintento
  automático tras la condición de caída; `roll_neg` usa esperas adaptativas por etapa y sale a
  retraerse en cuanto está erguido;
- **Verificado**: las cuatro direcciones se levantan directamente en unos 1-6 s; el mismo modelo
  impulsa la simulación MuJoCo y el gemelo en vivo del hardware ([página 09](./09-mujoco.md)).

## 1.2 Vista general

| Elemento | Especificación |
|---|---|
| Base | ~88 × 82 mm, 68 mm de alto (placa inferior + soporte del servo de hombro, impresos en 3D) |
| Brazo | Eje del hombro a 56 mm sobre la base, codo a 40.1 mm sobre el hombro; puntal del antebrazo ~17 cm (tubo de 12 mm) |
| Masa | ~133 g (tabla de masas del modelo: foot 92.1 / arm1 20.7 / arm2 20.1 g, incluidos ambos servomotores) |
| Hombro | PTK7452MG; límites manuales `[-1.85, +1.82]` rad (rango articular en simulación `[-1.07, +2.07]`) |
| Codo | PTK7452MG; límites manuales `[-0.90, +0.70]` rad (mecánico ~±1.55 rad) |
| Controlador | ESP32-S3-DevKitC-1 (framework Arduino / PlatformIO) |
| Actitud | IMU de 6 ejes Juxi ICM42670P (dirección I²C 0x23, 100 kHz) |
| Control de servos | LEDC del ESP32, 50 Hz, 14 bits, ancho de pulso 500–2500 µs |

## 1.3 Lista de materiales

| Categoría | Pieza | Cant. | Notas |
|---|---|---|---|
| Estructura | Impresión 3D: placa inferior, soporte del servo de hombro, soporte del servo de codo, puntal superior | 1 de cada | PETG o PLA, 15 % de relleno; los brazos de servo son los incluidos con los servomotores |
| Accionamiento | Servomotor PWM de 180° PTK7452MG | 2 | Engranaje metálico, 25T, ~12.2 g, ~3.4 kg·cm a 6 V |
| Controlador | ESP32-S3-DevKitC-1 | 1 | USB-C |
| Sensor | Módulo IMU Juxi ICM42670P | 1 | Alimentación de 3.3 V |
| Adaptador | Placa adaptadora de servos pasiva | 1 | GPIO → conectores de 3 pines, V+/GND compartidos, sin PCA9685 |
| Cableado | Cable de datos USB-C, cables Dupont, extensiones de servo | varios | — |
| Alimentación | Fuente para servos 5 V / ≥5 A | 1 | Una fuente de 5 V alimenta el ESP32 y los servos mediante un cable 1 a 2 (masa común); **verificada para las cuatro direcciones de incorporación** |

---

[← Volver al índice del tutorial](./index.md)
