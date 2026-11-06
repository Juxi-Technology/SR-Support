---
title: 06 Depuración y calibración
description: Formato de telemetría, comprobaciones de IMU y servos, calibración de giroscopio+acelerómetro, comprobación del centro, cuatro posturas tumbadas y la condición de caída, criterios de finalización.
---

# 06 Depuración y calibración

> **Los usuarios de unidad acabada pueden omitir esta página**: la fábrica calibra y verifica
> cada unidad. Repite estos pasos solo tras sustituir un servo/IMU, remontar un brazo de servo,
> o cuando se sospeche que una actualización de firmware ha alterado la calibración.

Esta es la **comprobación funcional y calibración del robot completo** tras el montaje, el
flasheo y la puesta a cero; recórrela en orden antes de usar el robot.

> **Alimentación durante la depuración**: el USB solo lleva datos serie. `c` necesita únicamente
> la IMU (los servos pueden estar sin alimentar); `t` / `z` / `e` necesitan el riel de servos de
> 5 V encendido. Si no quieres que el ESP32 reciba de dos fuentes, desconecta la rama de 5 V al
> ESP32, aliméntalo solo por USB y deja que la fuente de 5 V alimente únicamente los servos: es
> una configuración normal, véase la [página 04, sección 4.4](./04-assembly.md).

## 6.1 Abrir el puerto serie y leer la telemetría

En la carpeta `SR-Support` con `.venv` activado, abre el puerto serie (`COM27` es tu puerto):

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Las herramientas serie / la descarga de UartAssist para Windows están en la
[página 03, sección 3.3](./03-build-flash.md).)

Tras abrir el puerto, si la placa acaba de encenderse o pulsaste RST verás primero el registro
de arranque; si no hay registro de arranque, pulsa RST una vez. Después, una línea de telemetría
cada 250 ms:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Campo | Significado | Cómo leerlo |
|---|---|---|
| `up` | Vector «arriba» del mundo en coordenadas del cuerpo (x adelante, y izquierda, z arriba) | vertical `(0,0,1)`, inclinación≈0°; posturas tumbadas en 6.5 (p. ej. `(-1,0,0)`=pitch_pos) |
| `w` | Velocidad angular (rad/s) | ≈0 en reposo; distinta de cero al levantarse/rodar; la condición de caída necesita `|w|<0.9` |
| `q` | Ángulos de **consigna** articulares actuales (hombro, codo, rad; sin realimentación) | q=0 es brazo vertical; hombro + → brazo grande hacia −Y, codo + → antebrazo hacia +X |
| `qd` | Velocidades de consigna articulares | rara vez necesarias |
| `mode` | Modo de ejecución | `run` / `hold` / `manual` / `auto` |

Lecturas de ejemplo (ventana de `hw_watch`):

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

`tilt` es el ángulo entre el vector «arriba» y la vertical (a partir de `up_z`); 0° significa
completamente vertical.

Si el flujo que va pasando es difícil de leer, usa la ventana en vivo de línea fija (los
comandos siguen funcionando):

```bash
python tools/hw_watch.py --port COM27
```

Redibuja en el sitio up/inclinación, velocidad angular, ángulos articulares, modo y el último
evento; escribe en `cmd>` y pulsa Intro para enviar un comando, y los eventos también se añaden
a `logs/hw_watch.log`. Para una ejecución de incorporación completa en la que importa cada
línea cruda, sigue usando `pio device monitor` o `tools/hw_monitor.py` (este último escribe un
resumen en el registro cada 5 s).

**Cómo enviar comandos por puerto serie**: mantén abierto el monitor y escribe el comando
seguido de Intro (los comandos de un solo carácter no necesitan comillas). Comandos usados en
esta página:

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

La tabla completa de comandos está en la [página 03, sección 3.4](./03-build-flash.md).

**Script de autocomprobación rápida** (cierra antes el monitor serie para liberar el puerto):

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

El primer comando lee 0.6 s de telemetría; durante `--tilt 8`, inclina el robot a mano y el
script imprime los rangos de up/giroscopio y el rango de inclinación, lo que revela una IMU
bloqueada o mal orientada.

## 6.2 Comprobaciones y calibración de la IMU

`c` hace dos cosas:

1. **Sesgo cero del giroscopio**: promedia 200 muestras en reposo (unos 2 s) en el desfase de
   velocidad cero; se usa para el ciclo de alimentación actual y se rehace automáticamente en
   cada arranque;
2. **Cero del acelerómetro**: a partir de las mismas muestras promedia el vector de gravedad,
   exige que el robot esté nivelado (gravedad enteramente en +Z), lo valida y lo guarda en NVS
   (se recarga al arrancar).

Procedimiento (no hace falta alimentar los servos):

1. Haz primero la comprobación de orientación mecánica de la
   [página 04, sección 4.5](./04-assembly.md) (eje del hombro hacia −Y de la IMU, eje del codo
   hacia +X de la IMU);
2. Coloca el robot en posición vertical sobre una mesa NIVELADA, sin tocarlo y sin cables que
   tiren;
3. Escribe `c` y pulsa Intro en el monitor serie o en el `cmd>` de `hw_watch`:

   ```text
   c
   ```

4. Permanece quieto unos 2 s; el éxito imprime:

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

5. `accel cal rejected: |a|=...` significa que el robot no estaba nivelado o no estaba quieto
   (la norma de la gravedad se aleja más de 1.5 m/s² de 9.8); el sesgo queda sin cambiar:
   vuelve a colocarlo y reenvía `c`.

Verificación:

- Inclina lentamente a izquierda/derecha y adelante/atrás: las componentes x/y de `up` deben
  seguir el movimiento con suavidad; si una dirección está invertida, envía `i` / `j` para
  invertir el signo del eje de la IMU y ejecuta `c` de nuevo;
- Tumba el robot y espera 2 s: `up` debe coincidir con la tabla de posturas tumbadas de 6.5
  (p. ej. `(0,-1,0)` = roll_neg) con la cara de la base plana;
- Una inclinación persistente de 5° o más estando tumbado suele significar que el cero del
  acelerómetro está mal: repite esta sección.

> Las unidades acabadas se calibran en fábrica (guardado en NVS); repite esto solo tras
> sustituir/remontar la IMU o cuando la postura tumbada se vea claramente inclinada. `c` solo
> calibra la IMU: no cambia el cero de los servos (eso es la [página 05](./05-zero-tool.md)).
>
> Si usaste comandos manuales antes de calibrar (la telemetría termina en `manual`), `c` deja el
> robot en `hold`/`manual` y la condición de caída no iniciará una incorporación; mantenlo vertical
> y envía `g` para reanudar, o reinicia la placa.

## 6.3 Comprobaciones de los servos y autoprueba de direcciones

| Comprobación | Método | Esperado |
|---|---|---|
| Centros | `k` | `centers: shoulder 1681 us, elbow 1456 us` (valores de centro visual grabados en 2026-11; vuelve a poner a cero según la [página 05](./05-zero-tool.md)) |
| Ajuste fino del hombro | `o` / `p` (±10 µs) | Brazo vertical con `q=0` |
| Dirección | `m 0.5 0` / `m 0 0.5` | Hombro + → brazo grande hacia −Y; codo + → antebrazo hacia +X |
| Inversión de signo | `v` (hombro) / `b` (codo) | Solo si una dirección está invertida |
| Autoprueba | `t` | Movimiento pequeño en ambas articulaciones y luego centro |
| Punto neutro | `m 0 0` o `r` | Brazo vertical |

Límites articulares:

- Comandos manuales de hombro `[-1.85, +1.82]` rad; codo mecánico `±1.55` rad (alcanzable por
  el ejecutor);
- Los comandos manuales `m` recortan el codo a `[-0.90, +0.70]` rad;
- Salida PWM de 500–2500 µs a 50 Hz.

Escríbelos uno a uno en el **cuadro de envío** del monitor/asistente serie (Intro tras cada uno):

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Confirma: hombro `q>0` → brazo grande hacia **−Y**; codo `q>0` → antebrazo hacia **+X**.
Dirección incorrecta: inviértela con `v` / `b`, o vuelve a montar el brazo de servo.

## 6.4 Comprobación del centro

Grabado en fábrica (hombro 1681 µs / codo 1456 µs): **opcional para una unidad de fábrica**. En
un montaje DIY ya se hizo con la [calibración de punto cero de la página 05](./05-zero-tool.md)
y los valores se grabaron en `config.h` (vuelve a flashear si cambiaron); aquí basta ejecutar
`k` para confirmar que los centros coinciden con los valores grabados. Vuelve a la página 05
solo tras reindexar un brazo de servo, remontar, o si el brazo ya no descansa en el centro
visual.

## 6.5 Cuatro posturas tumbadas y la condición de caída

| Postura | `up` en el monitor | Significado físico |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | La parte superior del cuerpo apunta hacia +X |
| `pitch_neg` | `(+1, 0, 0)` | La parte superior del cuerpo apunta hacia −X |
| `roll_pos` | `(0, +1, 0)` | La parte superior del cuerpo apunta hacia −Y |
| `roll_neg` | `(0, -1, 0)` | La parte superior del cuerpo apunta hacia +Y |

Condición de la condición de caída (firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Solo entonces imprime `getup start pose=...` y comienza. Así que coloca el robot, suéltalo y
déjalo quieto ~0.5 s; agitarlo justo después de colocarlo suele significar que una mano aún lo
toca o que el cuerpo sigue rodando.

Comprobación: coloca el robot en cada una de las cuatro posturas, suelta y mantén quieto; en
0.5 s el registro serie debe mostrar `getup start pose=<matching pose>`.

## 6.6 Criterios de finalización

- [ ] `c` imprime `accel bias ... (saved)`;
- [ ] `t` muestra direcciones correctas en ambas articulaciones;
- [ ] `k` coincide con los centros grabados (o volviste a poner a cero según la página 05 y lo grabaste);
- [ ] las cuatro posturas tumbadas disparan `getup start`.

---

[← Volver al índice del tutorial](./index.md)
