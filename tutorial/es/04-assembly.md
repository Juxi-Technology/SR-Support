---
title: 04 Montaje: imprimir, construir, cablear
description: Impresión, reindexado y centrado de los brazos de servo, tabla de cableado, orientación de montaje de la IMU y orden de encendido del SR-Support.
---

# 04 Montaje: imprimir, construir, cablear

> **Los usuarios de unidad acabada pueden omitir esta página**: la fábrica ya ha impreso,
> montado, cableado e inspeccionado la unidad (véase la sección de estado de fábrica en el
> [índice](./index.md)). Sigue esta página solo si construyes desde piezas o sustituyes
> componentes.

## 4.1 Impresión e inspección

1. Imprime la placa inferior, el soporte del servo de hombro, el soporte del servo de codo y el
   puntal superior (1 de cada);
2. Comprueba con calibre el contorno de la base (~88 × 82 mm) y la altura total (~68 mm);
3. Prueba el encaje de los brazos de servo de 25T en sus ranuras; fíjalos con tornillos solo
   cuando no haya agarrotamiento;
4. Pesa cada pieza impresa y anótala frente a `hardware/v1/meshes/print_mass_model.json`.

## 4.2 Preparación de los servos (cero del firmware e instalación de los brazos)

1. **Cablea y flashea primero**: cablea ambos servos, la IMU, la alimentación de los servos y la
   masa común según la tabla de 4.4 (las piezas mecánicas aún sin montar; el firmware principal
   necesita la IMU para arrancar) y luego flashea el firmware principal según la
   [página 03, sección 3.1](./03-build-flash.md);
2. **Enciende hasta el cero del firmware**: abre el puerto serie a 115200 (las herramientas
   serie / la descarga de UartAssist están en la [página 03, sección 3.3](./03-build-flash.md)) y
   enciende; tras el arranque el firmware lleva ambos servos a q=0 (pulsos centrales 1681 / 1456 µs).
   Cuando el registro muestre `servo start q: 0.00 0.00 rad` y `ready; send g to run` (o
   `autorun on: ...`), los servos están en el cero;
3. **Apaga**: corta la alimentación de los servos (el USB puede seguir conectado) y confirma que
   ambos servos están descargados;
4. **Instala los brazos**: monta el brazo del hombro de modo que el brazo superior quede
   vertical, y el brazo del codo de modo que el antebrazo quede alineado con él; aprieta y
   comprueba el recorrido completo a mano;
5. Convención de direcciones (coincide con el simulador): `shoulder +q` mueve el brazo grande
   hacia **−Y**, `elbow +q` mueve el antebrazo hacia **+X**; los valores por defecto del
   firmware son `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> Los centros del firmware 1681 / 1456 µs ya incluyen el reindexado del brazo de la calibración
> de fábrica: **no cuentes los dientes**; monta los brazos en el cero del firmware con el brazo
> vertical. Alternativamente (equivalente, opcional), escribe `e` en el cuadro de envío serie y
> pulsa Intro para llevar ambos servos al centro eléctrico de 1520 µs y montar ahí (véase la
> tabla de comandos de la [página 03](./03-build-flash.md)); en cualquier caso, el comando `z`
> de la [página 05](./05-zero-tool.md) realiza el punto cero preciso final.

> Montar en el cero del firmware es solo un **centrado grueso** (el estriado del brazo es
> discreto). El punto cero preciso debe fijarse tras el montaje completo y el flasheo del
> firmware principal ([página 03](./03-build-flash.md)) con la
> [herramienta de punto cero de la página 05](./05-zero-tool.md): declara la postura visualmente
> vertical como q=0 (`z` no usa la IMU y funciona en cualquier postura), luego graba los pulsos
> impresos en `config.h` y vuelve a flashear. Aunque el brazo no se haya montado perfectamente,
> esta puesta a cero lo corrige; solo cuando un lado se queda sin recorrido (el pulso se recorta
> en 500/2500 µs) hay que sacar el brazo y reindexarlo. El índice del brazo determina cómo se
> reparte el recorrido entre los dos lados; los límites manuales del firmware
> (`Q_SHOULDER_MIN/MAX`) deben coincidir con el recorrido real: no los amplíes. Tras la puesta a
> cero, desplaza todos los puntos de paso de las secuencias como se describe en la página 05, o
> las posturas físicas de incorporación se desviarán.

## 4.3 Montaje de la base y el brazo

1. Fija la placa inferior y el soporte del servo de hombro entre sí con tornillos M3 para formar
   la base (~68 mm de alto);
2. Instala el servo del hombro en el soporte del hombro, con el brazo hacia arriba;
3. Fija el soporte del servo de codo al brazo del hombro y aprieta (forma el brazo superior);
   instala el servo del codo en el soporte del codo;
4. Conecta el puntal superior (antebrazo) al brazo del codo;
5. Mueve el brazo a la vertical a mano (`q≈0`) y confirma que coincide con el centro del servo.

## 4.4 Cableado

| Dispositivo | Pin del ESP32-S3 | Adaptador | Notas |
|---|---|---|---|
| Adaptador 3V3 | 3V3 | Pin de señal S1 | el otro extremo a VCC de la IMU (3.3 V) |
| Señal del hombro | GPIO4 | S4 | PWM de 50 Hz |
| Señal del codo | GPIO5 | S5 | PWM de 50 Hz |
| SDA de la IMU | GPIO6 | Pin de señal S6 | el otro extremo a SDA de la IMU; I²C 0x23, 100 kHz |
| SCL de la IMU | GPIO7 | Pin de señal S7 | el otro extremo a SCL de la IMU; I²C 0x23, 100 kHz |
| GND de la IMU | GND | — (directo) | masa común |
| LED (opcional) | GPIO2 | — | LED de estado |
| Entrada de alimentación de 5 V | 5V / GND | — | cable 1 a 2: una rama al ESP32, otra a V+/GND del adaptador para los servos |
| Alimentación de los servos | — | Bornera V+/GND | 5 V / ≥5 A; **las tensiones superiores deben usar solo esta bornera, nunca el 5V del ESP32** |
| S2 / S3 | — | — | no conectados |

Notas:

- El adaptador es un paso pasivo: S1/S6/S7 llevan 3V3 / SDA / SCL en sus pines de señal, S4/S5
  llevan las señales de los servos; confirma el orden V+/GND/señal de cada conector: una
  polaridad invertida destruye los servos o la placa;
- Mantén los cables I²C cortos y lejos de los cables de los servos; las resistencias de
  pull-up del módulo son de 3.3 V;
- Con una fuente de **5 V** puedes alimentar el 5V/GND del ESP32 y derivar la misma fuente a
  V+/GND del adaptador para los servos; las tensiones superiores (6 V / 7.4 V) deben alimentar
  solo V+/GND del adaptador y el ESP32 debe alimentarse por USB;
- **Con una batería de 5 V alimentando el ESP32 puedes mantener el Type-C conectado**: en el
  esquema oficial del DevKitC-1 cada VBUS del USB llega a la red de 5V a través de un diodo
  Schottky, así que no hay retorno de corriente y el USB funciona como datos (más alimentación
  auxiliar). En una placa clónica que omita el diodo, o si no puedes confirmarlo, desconecta la
  rama de 5 V al ESP32 mientras flasheas y aliméntalo por USB (opción 2);
- **Alimentación durante la depuración / el flasheo (ambas son normales; elige una)**:
  1. la fuente de 5 V alimenta el ESP32 y los servos mediante el divisor, el USB solo lleva datos;
  2. más fácil de razonar: desconecta la rama de 5 V al ESP32, alimenta el ESP32 solo por USB y
     deja que la fuente de 5 V alimente únicamente los servos.
  Usa la opción 2 para flashear, monitorizar el puerto serie y la calibración `c`; la opción 1
  para el funcionamiento autónomo;
- En el primer encendido deja los servos desconectados, verifica la polaridad y la tensión de
  V+ con un multímetro, luego prueba un servo y después ambos;
- Orden de cableado: masa y señales → alimentación de 5 V (ESP32 y servos juntos) → USB para el
  puerto serie cuando haga falta. El orden inverso al apagar.

## 4.5 Orientación de montaje de la IMU

La IMU va fijada a la base con tornillos (su orientación no es ajustable), así que el firmware
habilita `IMU_YAW90` y convierte el vector «arriba» del marco de la IMU a coordenadas del cuerpo:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Comprobación de la orientación mecánica** (posible una vez montados los servos, antes de
encender): usando los ejes impresos en el módulo IMU / documentados para él,

- el **eje de salida** del servo del hombro (el eje sobre el que se monta el brazo; también
  llamado eje del brazo o eje del engranaje) apunta hacia **−Y** de la IMU;
- el eje de salida del servo del codo apunta hacia **+X** de la IMU.

De abajo arriba, los dos servos son **hombro (inferior) → codo (superior)**; no los intercambies
al montar los brazos ni al cablear.

Estas dos direcciones son los ejes de hombro y codo del cuerpo; si no coinciden con el hardware,
la IMU o un soporte de servo está instalado al revés: corrígelo antes de encender.

Tras el encendido, vuelve a comprobarlo en la [página 06](./06-debug-and-calibrate.md): en
posición vertical da `up≈(0, 0, 1)`; las cuatro posturas tumbadas están en la tabla de 6.5.

---

[← Volver al índice del tutorial](./index.md)
