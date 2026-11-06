---
title: 09 Resolución de problemas
description: Síntomas, causas y soluciones habituales del SR-Support, incluyendo IMU, puerto serie, condición de caída, tiempos de espera del ejecutor y WiFi.
---

# 09 Resolución de problemas

Los comandos serie se envían mediante un asistente/monitor serie: escríbelos en el cuadro de
envío y pulsa Intro (activa «enviar nueva línea» en UartAssist); las herramientas serie / la
descarga de UartAssist para Windows están en la [página 03, sección 3.3](./03-build-flash.md).

## 9.1 Síntomas habituales

| Síntoma | Causa probable | Solución |
|---|---|---|
| `waiting for IMU startup 5000 ms...` y luego `IMU not ready` | Arranque lento de la IMU, cableado defectuoso, dirección incorrecta | Espera 5–10 s; comprueba 3V3, SDA=GPIO6 / SCL=GPIO7, dirección 0x23 |
| `IMU lost -> bus reset + re-init` repetido | Cables I²C largos o flojos | Acorta los cables, reasienta las conexiones |
| El flasheo falla con `could not open port` / `Access is denied` | El puerto serie lo ocupa el monitor o el asistente serie | Cierra antes `hw_monitor.py` o el monitor serie |
| El robot no arranca tras colocarlo | El cuerpo no está quieto, o una mano lo toca | Suelta y mantén quieto ≥0.5 s; espera `getup start` |
| Agitación inmediata / dirección incorrecta | La condición de caída se disparó a mitad de rodadura, clasificación errónea | Colócalo y suéltalo limpiamente; reintenta |
| La ejecución se detiene e imprime `executor timeout` tras 14 s | La referencia no terminó | Respaldo normal; reintento automático tras 1.5 s; conserva el registro |
| Eventos `executor re-plan` ocasionales | Respaldo normal tras una presión de `roll_neg` fallida | Comprueba si termina con `done` |
| El servo zumba / se calienta | Bloqueo o objetivo que agarrota | Envía `x` o corta la alimentación; comprueba límites y holgura mecánica |
| El brazo golpea el cuerpo durante el auto-enderezamiento | Movimiento grande del hombro | Comprueba `Q_SHOULDER_MAX` y la holgura; mantén la altura de base de ~68 mm |
| `up` no coincide con la postura real (inclinación persistente de 5°+ estando tumbado) | Desfases de cero del acelerómetro sin calibrar | Pon el robot nivelado y envía `c` (véase la [página 06, 6.2](./06-debug-and-calibrate.md)) |
| El brazo no descansa en el centro visual tras retraerse | Cero desplazado (reindexado/remontado sin volver a poner a cero) | Vuelve a poner a cero con la [herramienta de la página 05](./05-zero-tool.md) y graba el valor |
| El servo zumba/castañetea tras una incorporación | Autoexcitación transitoria del servo analógico tras movimiento grande/bloqueos (la salida es constante) | Se amortigua solo; añade arandelas de goma amortiguadoras o usa un servo digital; sujetar el brazo lo silencia al instante |
| Página de estado / aprovisionamiento inaccesible | Proxy del navegador no eludido, o punto de acceso apagado | Añade `192.168.4.1` a las excepciones del proxy; envía `w` para activar el WiFi |

## 9.2 Comandos de seguridad

| Situación | Comando |
|---|---|
| Detener el movimiento de inmediato | `s` (mantener el último objetivo) o `x` (desacoplar el PWM, liberar el par) |
| Recuperarse tras `x` | `r` reinicializa el PWM y centra |
| Una articulación se mueve al revés | Inversión de signo con `v` (hombro) / `b` (codo) |

## 9.3 Capturar un fallo

Conserva la parte correspondiente de `logs/hw_monitor.log`. Las líneas clave son:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```

---

[← Volver al índice del tutorial](./index.md)
