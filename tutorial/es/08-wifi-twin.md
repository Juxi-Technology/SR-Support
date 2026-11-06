---
title: 08 WiFi y el gemelo de simulación
description: Página de estado, aprovisionamiento de la red doméstica, el gemelo en vivo MuJoCo inalámbrico y el registro de telemetría por WiFi.
---

# 08 WiFi y el gemelo de simulación

Este paso es opcional y no es necesario para el auto-enderezamiento en sí.

## 8.1 Punto de acceso y página de estado

Punto de acceso: SSID `SR-Support`, contraseña `srsupport`, dirección `192.168.4.1` (`w` lo
alterna; activado por defecto al arrancar). `w` se envía por puerto serie: escribe `w` en el
cuadro de envío del monitor/asistente serie y pulsa Intro; las herramientas serie / la descarga
de UartAssist para Windows están en la [página 03, sección 3.3](./03-build-flash.md).

Únete al punto de acceso y abre `http://192.168.4.1` (los teléfonos suelen abrir el portal
automáticamente). La página se actualiza cada 300 ms: estado, vector «arriba» y barra de
verticalidad, consignas articulares, postura/fase de incorporación, estado de la WiFi doméstica
y el interruptor del flujo del gemelo. Si el navegador usa un proxy, añade una excepción para
esta dirección.

## 8.2 Aprovisionamiento (unirse a la WiFi doméstica)

En la página de estado usa la tarjeta Home WiFi: `Scan` → elige una red → introduce la
contraseña → `Connect`. Si tiene éxito, el ESP32 funciona en AP+STA:

- el punto de acceso sigue activo (el trabajo en banco no se ve afectado);
- el robot es accesible en la LAN doméstica (la página muestra su `Robot IP`);
- las credenciales se guardan en NVS y se reconectan automáticamente al arrancar.

Solo 2.4 GHz; los escaneos/conexiones se rechazan mientras una incorporación está en curso.

## 8.3 Gemelo en vivo MuJoCo inalámbrico

Pulsa `Twin ON` en la página de estado (equivale al comando serie `d`) y luego:

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(En la carpeta `SR-Support`; crea y activa `.venv` primero como en la
[página 02](./02-environment.md): allí también se prepara el entorno de las herramientas.)

- La ventana refleja la actitud real en vivo y mantiene el cuerpo sobre el suelo;
- El brazo se mantiene en su ángulo de contacto con el suelo como el servo bloqueado (sin
  penetrar el suelo);
- El cable USB solo hace falta para flashear y volcar registros;
- Reproduce un registro grabado sin conexión con `--replay <file>`.

## 8.4 Registro de telemetría por WiFi

```bash
python tools/tcp_log.py
```

Guarda el flujo de telemetría del punto de acceso en `logs/wifi_<time>.txt` para reproducción y
análisis sin conexión.

## 8.5 Referencia de simulación y entrenamiento

El repositorio incluye el modelo MuJoCo y el código de entrenamiento (`training/b_line/`) para
reproducción y reentrenamiento; los archivos del modelo se describen en la
[página 10](./10-reference.md).

---

[← Volver al índice del tutorial](./index.md)
