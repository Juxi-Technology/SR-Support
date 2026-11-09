---
title: 09 Simulación MuJoCo y el gemelo en vivo
description: La ventana de simulación MuJoCo local (repetición de incorporación de las cuatro posturas), el gemelo en vivo WiFi del robot real y el registro de telemetría.
---

# 09 Simulación MuJoCo y el gemelo en vivo

MuJoCo se usa de dos maneras en este proyecto, ambas con `hardware/v1/robot_v1.xml` (el modelo
del robot real de la misma fuente):

- **Simulación local**: sin ningún robot conectado, repite en bucle las cuatro posturas
  tumbadas y sus incorporaciones en el ordenador para validar las secuencias de referencia y
  observar el movimiento;
- **Gemelo en vivo**: el robot real transmite su actitud por WiFi y la ventana de MuJoCo
  refleja el movimiento real en tiempo real (un gemelo digital).

La ventana funciona igual en ambos casos: arrastra con el botón izquierdo para rotar la vista,
con el botón derecho para desplazarla y usa la rueda para hacer zoom. Antes del primer uso,
crea y activa el `.venv` como en la [página 02](./02-environment.md) e instala en él las
dependencias de las herramientas (`pip install -r tools/requirements.txt`, véase la página 02).

## 9.1 Ventana de simulación local

En la carpeta `SR-Support` (con `.venv` activado):

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

La ventana se titula `MuJoCo : sr_support_v1` (figura 9-1). El robot se coloca sucesivamente en
las cuatro posturas tumbadas (`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`); cada vez, el
ejecutor ejecuta la secuencia de referencia con exactamente los parámetros del firmware hasta
que el robot se levanta, y luego se fija la siguiente postura. El bucle se repite hasta que
cierres la ventana. El terminal imprime la postura y el resultado:

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` significa que la postura se levantó en simulación. Con `ok=False`, comprueba la
secuencia de referencia y cualquier parámetro que hayas cambiado contra la
[página 06](./06-debug-and-calibrate.md).

![Figura 9-1 La ventana de simulación MuJoCo (repetición de incorporación de las cuatro posturas)](../images/sr-support/mujoco/01-mujoco-window.png)

*Figura 9-1: un fotograma del bucle de las cuatro posturas: el ejecutor levanta una postura tumbada.*

> Diferencia conocida del modelo: con el modelo de masa 1×, `roll_neg` imprime `ok=False` en
> simulación (la masa y la fricción del brazo del modelo difieren de las del robot real, véase
> la [página 11](./11-reference.md) 11.4); esto no afecta al firmware real.

## 9.2 Gemelo en vivo por WiFi

Requisito previo: el robot se ha unido a la red doméstica como en la [página 08](./08-wifi.md)
y el ordenador está en la misma red. La página de estado muestra la dirección del robot como
`Robot IP`; cópiala en el comando siguiente.

1. En la página de estado pulsa `Twin ON` (equivale al comando serie `d`);
2. En la carpeta `SR-Support` con `.venv` activado, ejecuta (sustituye la dirección por la
   `Robot IP` de la página de estado):

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

El modelo refleja la actitud real en vivo (flujo de cuaterniones a 50 Hz) y mantiene el cuerpo
sobre el suelo; el brazo se mantiene en su ángulo de contacto con el suelo como el servo
bloqueado, de modo que nunca penetra el suelo.

- Ordenador conectado directamente al punto de acceso del robot: la dirección es siempre
  `192.168.4.1`, `python tools/live_twin.py --tcp 192.168.4.1:3333`;
- Alternativa con cable: `python tools/live_twin.py --port COM27` (la herramienta envía `d`
  para activar el flujo automáticamente);
- Reproducción sin conexión: `python tools/live_twin.py --replay logs/hw_fast_xxx.txt`;
- El gemelo es de solo lectura salvo por la conmutación del flujo: nunca envía comandos de
  control.

## 9.3 Registro de telemetría

```bash
python tools/tcp_log.py
```

Guarda el flujo de telemetría en `logs/wifi_<time>.txt` para reproducción sin conexión
(`--replay`) y análisis de fallos. En el punto de acceso se conecta por defecto a
`192.168.4.1:3333`; en la red doméstica pasa la `Robot IP` de la página de estado:

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 Referencia de simulación y entrenamiento

`training/b_line/` incluye el ejecutor, las secuencias de referencia y el entorno de simulación
—idénticos valor por valor al firmware— para reproducción, validación y ajuste de parámetros;
los archivos del modelo se describen en la [página 11](./11-reference.md) 11.1.

---

[← Volver al índice del tutorial](./index.md)
