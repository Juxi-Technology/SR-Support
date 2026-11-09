---
title: 08 Página de estado WiFi y aprovisionamiento
description: Punto de acceso, página de estado y aprovisionamiento de la red doméstica; la simulación MuJoCo y el gemelo en vivo se tratan en la página 09.
---

# 08 Página de estado WiFi y aprovisionamiento

Este paso es opcional y no es necesario para el auto-enderezamiento en sí. La ventana de
simulación MuJoCo y el gemelo en vivo tienen su propia página: [página 09](./09-mujoco.md).

## 8.1 Punto de acceso y página de estado

Punto de acceso: SSID `SR-Support`, contraseña `srsupport`, dirección `192.168.4.1` (`w` lo
alterna; activado por defecto al arrancar). `w` se envía por puerto serie: escribe `w` en el
cuadro de envío del monitor/asistente serie y pulsa Intro; las herramientas serie / la descarga
de UartAssist para Windows están en la [página 03, sección 3.3](./03-build-flash.md).

Únete al punto de acceso y abre `http://192.168.4.1` (los teléfonos suelen abrir el portal
automáticamente). La página se actualiza cada 300 ms: estado, vector «arriba» y barra de
verticalidad, consignas articulares, postura/fase de incorporación, estado de la WiFi doméstica
y el interruptor del flujo del gemelo (espejo en vivo en la [página 09](./09-mujoco.md)). Si el
navegador usa un proxy, añade una excepción para esta dirección.

![Figura 8-1 La página de estado del robot](../images/sr-support/wifi/01-status-page.png)

*Figura 8-1: la página de estado del robot (abierta en el navegador en la dirección del robot). En esta captura el robot se ha unido al WiFi doméstico: la tarjeta Home WiFi muestra el estado de conexión y la Robot IP, y debajo está el interruptor del flujo del gemelo (uso en 9.2).*

## 8.2 Aprovisionamiento (unirse a la WiFi doméstica)

En la página de estado usa la tarjeta Home WiFi: `Scan` → elige una red → introduce la
contraseña → `Connect`. Si tiene éxito, el ESP32 funciona en AP+STA:

- el punto de acceso sigue activo (el trabajo en banco no se ve afectado);
- el robot es accesible en la LAN doméstica (la página muestra su `Robot IP`; usa esa dirección en el comando del gemelo de la página 09);
- las credenciales se guardan en NVS y se reconectan automáticamente al arrancar.

Solo 2.4 GHz; los escaneos/conexiones se rechazan mientras una incorporación está en curso.

---

[← Volver al índice del tutorial](./index.md)
