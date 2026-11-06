---
title: 07 Uso y monitorización del auto-enderezamiento
description: Cómo operar el SR-Support en cada dirección de caída, tiempos de movimiento esperados, eventos por puerto serie y registros de monitorización.
---

# 07 Uso y monitorización del auto-enderezamiento

> Todas las unidades acabadas se prueban en las cuatro direcciones antes de enviarse. Para el
> primer uso, verifica igualmente cada dirección una vez según la sección 7.2 para asegurarte de
> que la unidad está sana tras el transporte.

## 7.1 Procedimiento

1. Enciende con el robot en posición vertical y espera `autorun on: get-up waits for a fall`;
2. Derriba el robot en cualquier dirección, **suéltalo y mantenlo quieto unos 0.5 s**;
3. Cuando aparezca `getup start pose=<pose>`, el ejecutor arranca automáticamente;
4. Si tiene éxito, el firmware imprime `standing -> executor done` y vuelve a la espera;
5. Si una ejecución supera 14 s, el firmware imprime `executor timeout`; tras 1.5 s de enfriamiento
   la condición de caída se vuelve a disparar y reintenta.

## 7.2 Comportamiento esperado por dirección

| Postura | Mecanismo | Tiempo en el robot real |
|---|---|---|
| `pitch_neg` (arriba → −X) | El codo se apoya, la carrera del hombro apalanca el cuerpo hacia arriba | ~3 s |
| `pitch_pos` (arriba → +X) | Mismo levantamiento; si vuelca durante la retracción, la replanificación de postura ejecuta `pitch_pos` de nuevo | ~5–6 s |
| `roll_pos` (arriba → −Y) | Palanca directa del hombro usando el lado de recorrido largo | ~3 s |
| `roll_neg` (arriba → +Y) | **Presión directa a recorrido completo → bombeos de cuña de codo ×2 → reintento de latigazo si hace falta**; sin volcar por encima | ~2–6 s |

> El firmware anterior volcaba `roll_neg` por encima y replanificaba a un levantamiento de pitch
> (5–14 s); la compilación actual usa el espejo de la presión de +Y, así que las cuatro
> direcciones son simétricas y comparables en velocidad. Un ocasional
> `executor re-plan roll_neg -> ...` solo significa que esa presión falló y entró el reintento de
> respaldo: es la red de seguridad normal.

## 7.3 Lógica del ejecutor (en el firmware)

- 20 ticks (0.4 s) por punto de paso de referencia, interpolación lineal; límite de giro de la
  salida 0.08 rad/tick;
- Tras los puntos de paso, retrae el brazo al punto neutro a 0.033 rad/tick;
- Terminado cuando `up_z > 0.95` con el objetivo en cero durante 50 ticks;
- Si el cuerpo se asienta sobre otro eje tumbado (`up_z<0.6`, `|ω|<0.8` durante 15 ticks),
  retrae al neutro y cambia a la referencia de la nueva postura (hasta 5 cambios);
- La referencia de `roll_neg` usa **esperas adaptativas por etapa**: las etapas de presión/bombeo
  esperan mientras `up_z<0.92`, hasta un tope de ticks por etapa (presión 40 / bombeo 30 /
  bombeo 30 / latigazo 40 / final 90); si el cuerpo se endereza a mitad de secuencia, el
  ejecutor salta directamente a la retracción para que las etapas posteriores no puedan tumbar
  al robot ya de pie.

## 7.4 Monitorización y registros

```bash
python tools/hw_monitor.py COM27
```

(Ejecútalo en la carpeta `SR-Support` con `.venv` activado: [página 02](./02-environment.md).
Cierra antes cualquier asistente/monitor serie; las herramientas serie / la descarga de
UartAssist para Windows están en la [página 03, sección 3.3](./03-build-flash.md).)

- Añade eventos y resúmenes de telemetría cada 5 segundos a `logs/hw_monitor.log`;
- Registra `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost`, etc.;
- Comprueba la envolvente de los servos (hombro `[-1.85,+1.82]`, codo `±1.55`) y escribe `!! VIOLATION`;
- Mientras el ejecutor funciona, imprime una traza cada 0.2 s:

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Campo | Significado |
|---|---|
| `pose` | Postura de referencia actual |
| `ph` / `tick` | Fase del punto de paso / tick dentro de la fase |
| `tgt` | Ángulos articulares objetivo |
| `up` | Vector «arriba» actual |
| `q` | Consigna articular actual |
| `sw` | Número de cambios de postura hasta ahora |

> Abrir el monitor reinicia el ESP32; ciérralo antes de flashear.

## 7.5 Registro de pruebas

Para cada prueba anota la postura, si terminó con `done`, la duración, el número de cambios y
cualquier violación. `logs/hw_monitor.log` es el registro autoritativo.

---

[← Volver al índice del tutorial](./index.md)
