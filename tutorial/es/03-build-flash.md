---
title: 03 Flashear el firmware principal
description: Flashea el firmware de la línea B del SR-Support desde el bin precompilado (Flash Download Tool / esptool) o compílalo con PlatformIO; comandos por puerto serie y registro de arranque.
---

# 03 Flashear el firmware principal

> **Los usuarios de unidad acabada pueden omitir esta página**: la fábrica ya ha flasheado y
> verificado el firmware. Solo hay que repetirlo para actualizaciones de firmware o tras
> modificar el código. Los clientes usan la imagen precompilada (3.1, sin PlatformIO); los
> desarrolladores compilan desde fuentes (3.2).

## 3.1 Flashear la imagen precompilada (recomendado para clientes)

1. Asegúrate de tener `firmware/releases/sr_support_b_ptk_factory.bin` (sumas de verificación en
   `SHA256SUMS`, junto a él);
2. Entra en modo descarga: mantén **BOOT**, pulsa **RST**, suelta **BOOT**;
3. Flashea la imagen (configuración de la herramienta en la [página 02, sección 2.4](./02-environment.md);
   ejecuta estos comandos en la carpeta `SR-Support` con `.venv` activado):
   - GUI de Windows: Flash Download Tool → ESP32-S3 → carga el bin en `0x0` → START;
   - línea de comandos Windows / Linux / macOS:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Pulsa RST al terminar y lee el registro como en 3.3.

> Para el flasheo / la depuración por puerto serie puedes alimentar el ESP32 por USB y dejar la
> fuente de 5 V solo para los servos (las dos opciones de alimentación están en la
> [página 04, sección 4.4](./04-assembly.md)).

> El comando es **idéntico en Windows / Linux / macOS**; solo cambia el puerto:
> `COM27` en Windows, `/dev/ttyACM0` en Linux, `/dev/tty.usbmodem*` en macOS.
> Flash Download Tool es solo para Windows; en los demás usa la línea de comandos de esptool.

> El centrado para el montaje no necesita una segunda imagen: tras flashear esta, enciende; ambos
> servos van al cero del firmware (1681 / 1456 µs); luego apaga e instala los brazos de servo
> ([página 04, sección 4.2](./04-assembly.md)). Opcionalmente, envía `e` para llevarlos primero
> al centro eléctrico de 1520 µs (equivalente).

## 3.2 Compilar y flashear desde fuentes (desarrolladores)

Entorno: [página 02, sección 2.5](./02-environment.md). Proyecto:
`firmware/sr_support_b_ptk/` (entorno `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Ejecútalos en la carpeta `SR-Support` con `.venv` activado (página 02, sección 2.3); son
> idénticos en las tres plataformas: sustituye `COM27` en `--upload-port` por tu puerto. Cierra
> cualquier cosa que ocupe el puerto serie (monitor serie, `tools/hw_monitor.py`) antes de
> flashear, o aparecerá `could not open port` / `Access is denied`.

Una compilación correcta usa aproximadamente 56 % de RAM y 30 % de flash (WiFi + servidor web
incluidos; las compilaciones anteriores sin WiFi eran de en torno al 7 % / 12 %).

## 3.3 Monitor serie

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Igual en las tres plataformas; sustituye `COM27` por tu puerto.)

> **Asistente serie con GUI para Windows (opcional)**: UartAssist de 野人家园 (gratuito, un
> solo exe, solo Windows). Página oficial <https://cmsoft.cn/resource/101.html>, entrada de
> descarga oficial <https://cmsoft.cn/resource/download/101>. Selecciona el puerto COM,
> **115200, 8N1, sin control de flujo**, activa «enviar nueva línea»; observa el registro de
> arranque/telemetría en el panel de recepción y escribe comandos en el cuadro de envío.
> Descárgalo solo desde el enlace oficial (los sitios de terceros suelen incluir adware); no
> hagas commit del exe en este repositorio.

**Visores de puerto serie para Linux / macOS (elige uno)**:

- Preferido: el comando `pio device monitor` de arriba (se instala con el proyecto, multiplataforma);
- CLI ligera: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` en macOS; sal con `Ctrl-]`); también funciona el
  `screen /dev/ttyACM0 115200` integrado (sal con `Ctrl-A` y luego `K`);
- GUI: **CoolTerm** (gratuito, Windows/macOS/Linux, sitio oficial
  <https://freeware.the-meiers.org>); en Linux también puedes `sudo apt install cutecom`.

> En Linux añade tu usuario al grupo `dialout`: `sudo usermod -aG dialout $USER`, y luego cierra
> sesión y vuelve a entrar.

Tras abrir el puerto, si la placa acaba de encenderse o pulsaste RST verás primero el registro
de arranque; si no, pulsa RST una vez. Tras el reinicio deberías ver:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Comandos por puerto serie (115200)

Escribe cada comando en el **cuadro de envío** del monitor/asistente serie y pulsa Intro
(activa «enviar nueva línea» en UartAssist); el comando `m` necesita un espacio y dos valores,
p. ej. `m 0.5 0`.

| Comando | Función |
|---|---|
| `g` | Iniciar/continuar la ejecución (esta compilación se autoinicia; normalmente no hace falta) |
| `s` | Detener el ejecutor, mantener el último objetivo |
| `x` | Liberación de emergencia: desacopla el PWM; rearma con `r` |
| `r` | Reinicializar el PWM y centrar |
| `t` | Autoprueba de servos (movimiento pequeño) |
| `c` | Calibrar giroscopio + **desfases de cero del acelerómetro** (el robot debe estar DE PIE Y NIVELADO y quieto; se guarda en NVS) |
| `m <q1> <q2>` | Objetivos articulares manuales en rad |
| `1/2` | Hombro manual ±0.5 rad |
| `3/4` | Codo manual ±0.5 rad |
| `0` | Punto neutro manual |
| `l` | Registro rápido de 3 s a 50 Hz |
| `k` | Imprimir los anchos de pulso centrales de ambos servos |
| `o` / `p` | Ajuste fino del centro del hombro ±10 µs |
| `z` | Punto cero tipo encoder: la postura actual pasa a ser q=0 para ambas articulaciones; imprime los nuevos pulsos (solo RAM; véase la [página 05](./05-zero-tool.md)) |
| `e` | Centro eléctrico (opcional): ambos servos a 1520 µs para montar los brazos de servo en el centro eléctrico; lo habitual es encender hasta el cero del firmware y montar ahí (véase la [página 04, 4.2](./04-assembly.md)) |
| `d` | Alternar el flujo del gemelo a 50 Hz (gemelo MuJoCo; el mismo interruptor en la página de estado) |
| `w` | Alternar WiFi (punto de acceso + página de estado/aprovisionamiento, véase la [página 08](./08-wifi-twin.md)) |
| `v` / `b` | Invertir el signo del hombro / codo |
| `i` / `j` | Invertir el signo X / Y de la IMU |
| `h` | Alternar el retorno a vertical (ruta de política heredada) |
| `a` | Modo heredado de prueba de incorporación mediante script |

## 3.5 Comportamiento al encender

El firmware define `AUTORUN_ON_BOOT`: tras el encendido, el ejecutor espera a que el robot esté
**completamente tumbado y quieto** durante 0.5 s y luego arranca automáticamente: no hace falta
`g`. Enciende con el robot en posición vertical.

---

[← Volver al índice del tutorial](./index.md)
