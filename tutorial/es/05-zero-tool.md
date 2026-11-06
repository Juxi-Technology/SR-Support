---
title: 05 Calibración de punto cero (teclas de flecha; obligatorio para montajes DIY)
description: Mueve el brazo hasta el centro visual con las teclas de flecha y decláralo q=0; obligatorio para todo montaje DIY y tras reindexar un brazo de servo o volver a montar.
---

# 05 Calibración de punto cero (teclas de flecha; obligatorio para montajes DIY)

Los ceros de los servos y los ceros de aceleración de la IMU se calibran y graban por unidad en
la fábrica, así que una unidad de fábrica no necesita nada de esta página. Un **montaje DIY debe
hacer esta página**: un brazo montado a mano casi nunca queda exactamente en el centro. Aunque
el brazo no se haya montado exactamente en el cero del firmware, puedes corregirlo aquí: mueve
el brazo hasta la vertical visual con las teclas de flecha y pulsa `z` para declarar la postura
**actual** como q=0. El comando `z` no usa la IMU y funciona en cualquier postura o índice de
brazo.

Vuelve aquí cuando: se haya reindexado un brazo de servo, el brazo se haya desmontado/vuelto a
montar, se haya sustituido un servo, se haya sustituido/remontado la IMU (recalibrar el
acelerómetro), o el brazo ya no descanse en el centro visual tras retraerse.

> `z` solo desplaza el cero del software; **no** cambia cómo reparte el recorrido el índice del
> brazo (PWM 500-2500 µs). Si tras la puesta a cero una dirección se queda sin rango (el pulso se
> recorta en 500/2500 µs y el brazo no alcanza un ángulo de secuencia necesario), reindexa el
> brazo (unos 2 dientes en el hombro) y vuelve a poner a cero.

Momento: después de montar el robot por completo y flashear el firmware principal (la ruta DIY
va 03 → 04 → 05).

## 5.1 Principio

El firmware define q=0 como el centro visual: brazo vertical, ambos eslabones en línea. El
comando `z` es un cero tipo encoder: hace que las posiciones articulares **actuales** sean q=0 e
imprime los anchos de pulso centrales correspondientes.

## 5.2 Procedimiento

1. Conecta tanto la batería como el USB (servos alimentados) y ejecuta esto en la carpeta
   `SR-Support` con `.venv` activado:

   ```bash
   python tools/hw_shoulder_range.py
   ```

   Cierra antes cualquier asistente/monitor serie (ocupan el puerto); las teclas en la ventana
   de abajo las lee esta herramienta, no hace falta asistente serie. Las herramientas serie / la
   descarga de UartAssist para Windows están en la
   [página 03, sección 3.3](./03-build-flash.md).

   Se actualiza en el sitio una pantalla persistente de cuatro líneas:

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Muévete con las teclas de flecha: `↑`/`↓` = brazo grande ±0.05 rad, `←`/`→` = brazo pequeño
   ±0.05 rad (Mayús = ±0.20) hasta que el brazo se vea **vertical y alineado**;
3. Pulsa `z`; el firmware imprime:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. Comprobación rápida: pulsa `n` (home), muévete un poco, vuelve a home; el brazo debe volver
   al centro visual que acabas de definir.

## 5.3 Grabado (obligatorio cuando estés conforme)

`z` solo toca la RAM; un reinicio restaura el cero antiguo. Cuando estés conforme:

1. Escribe los dos valores de pulso en `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. Desplaza todos los puntos de paso de `EXEC_REF*` y de `training/b_line/getup_reference_b39.py`
   con los mismos desfases (hombro/codo, cada uno −Δ rad);
3. Vuelve a flashear y prueba de nuevo las cuatro direcciones ([página 07](./07-self-righting.md)).

> Una pulsación equivocada es inofensiva: vuelve a poner a cero para sobrescribir.

## 5.4 Comandos relacionados

| Comando | Función |
|---|---|
| `z` | La postura actual pasa a ser q=0 para ambas articulaciones; imprime los nuevos pulsos centrales (solo RAM) |
| `k` | Leer los pulsos centrales actuales (hombro/codo, µs) |
| `o` / `p` | Ajuste fino en vivo del centro del hombro ±10 µs (se restablece al reiniciar) |

---

[← Volver al índice del tutorial](./index.md)
