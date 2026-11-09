---
title: Tutorial del robot auto-enderezante SR-Support
description: Tutorial completo del dispositivo auto-enderezante SR-Support de 2 GDL, desde los conceptos básicos y la preparación del entorno hasta el flasheo, el montaje, el punto cero, la calibración, el uso del auto-enderezamiento y la resolución de problemas.
---

# Tutorial del robot auto-enderezante SR-Support

[简体中文](../zh-hans/index.md) · [繁體中文](../zh-hant/index.md) · [English](../en/index.md) · [日本語](../ja/index.md) · [한국어](../ko/index.md) · [Deutsch](../de/index.md) · [Français](../fr/index.md) · [Español](../es/index.md) · [Italiano](../it/index.md) · [Português (BR)](../pt-br/index.md) · [Português (PT)](../pt-pt/index.md)


SR-Support es un dispositivo auto-enderezante activo de bajo coste basado en un brazo de 2 GDL.
Tras volcar en cualquier dirección, apoya su brazo de dos articulaciones en el suelo, rueda y se
endereza de nuevo. Este tutorial está organizado como un orden de lectura que cubre todo el
camino desde cero hasta una unidad verificada.

## Orden de lectura

| # | Página | Contenido | Nota |
|---|---|---|---|
| 01 | [Conceptos básicos](./01-basics.md) | Principio de funcionamiento, especificaciones, lista de materiales | leer primero |
| 02 | [Preparación del entorno](./02-environment.md) | Crear/activar `.venv`, firmware precompilado + herramientas de flasheo (Flash Download Tool / esptool), herramientas del lado del PC y entorno MuJoCo, PlatformIO opcional, puerto serie | **hacer esto primero** |
| 03 | [Flashear el firmware principal](./03-build-flash.md) | Binario precompilado (recomendado para clientes) o compilación desde fuentes con PlatformIO, comandos por puerto serie, comportamiento de arranque | opcional para unidades de fábrica |
| 04 | [Montaje: imprimir, construir, cablear](./04-assembly.md) | Piezas impresas, indexado del brazo de servo, tabla de cableado, montaje de la IMU | opcional para unidades de fábrica |
| 05 | [Calibración de punto cero](./05-zero-tool.md) | Ajuste fino con teclas de flecha + puesta a cero con `z` (tras reindexar/remontar) | **obligatorio para montajes DIY**; opcional para unidades de fábrica |
| 06 | [Depuración y calibración](./06-debug-and-calibrate.md) | Comprobación y calibración del robot completo: telemetría, IMU, servomotores, comprobación del centro, cuatro posturas tumbadas, condición de caída | |
| 07 | [Uso y monitorización del auto-enderezamiento](./07-self-righting.md) | Cuatro direcciones de caída, movimiento esperado, monitorización y registros | |
| 08 | [Página de estado WiFi y aprovisionamiento](./08-wifi.md) | Punto de acceso, página de estado, aprovisionamiento de la WiFi doméstica | opcional |
| 09 | [Simulación MuJoCo y gemelo en vivo](./09-mujoco.md) | Ventana de simulación local de las cuatro posturas, gemelo en vivo WiFi, registro de telemetría | opcional |
| 10 | [Resolución de problemas](./10-troubleshooting.md) | Síntomas y soluciones habituales | referencia |
| 11 | [Referencia: modelo, parámetros, licencias](./11-reference.md) | Archivos del modelo (XML/STL), parámetros, secuencias de referencia, licencias | referencia |

## Estado de fábrica de una unidad acabada (dos rutas de lectura)

Este tutorial sirve a dos públicos: elige la ruta que se ajuste al tuyo:

| Lector | Estado de fábrica | Ruta recomendada |
|---|---|---|
| **Usuario de unidad acabada** | Montada y cableada, firmware flasheado, **calibrada** (ceros de servo y ceros de aceleración de la IMU grabados), **probada** (las cuatro direcciones de incorporación verificadas unidad por unidad) | Ve directamente a [07 uso](./07-self-righting.md), [08 aprovisionamiento WiFi](./08-wifi.md) y [09 simulación MuJoCo y gemelo en vivo](./09-mujoco.md) (opcional); guarda [10](./10-troubleshooting.md)/[11](./11-reference.md) como referencia. **Las páginas 02/03/04/05/06 solo son necesarias para actualizaciones de firmware, sustitución de servo/IMU o remontaje del brazo de servo**; para usar las herramientas de gemelo/telemetría de la página 09, instala primero las herramientas del lado del PC de la página 02. |
| **Montador de kit / DIY** | Parte de piezas sueltas | Sigue [01](./01-basics.md) → [02](./02-environment.md) → [03 flasheo](./03-build-flash.md) → [04 montaje](./04-assembly.md) → [05 punto cero (obligatorio)](./05-zero-tool.md) → [06 depuración/calibración](./06-debug-and-calibrate.md) → [07](./07-self-righting.md) de principio a fin. Tanto el punto cero (05) como la calibración (06) se hacen **después del montaje completo y del flasheo**: `z` no usa la IMU y funciona en cualquier postura; `c` requiere el robot montado y nivelado. |

> Comprobación recomendada en el primer uso de una unidad acabada: enciéndela en posición
> vertical → confirma `up≈(0,0,1)` → vuelca una vez en cada una de las cuatro direcciones
> según la [página 07](./07-self-righting.md) y confirma que se levanta.

## Requisitos previos

- Piezas mecánicas de SR-Support (placa inferior, soporte del servo de hombro, soporte del servo de codo, puntal superior; impresión y montaje en la [página 04](./04-assembly.md));
- Placa ESP32-S3, IMU Juxi ICM42670P, placa adaptadora de servos de accionamiento directo pasivo;
- 2 servomotores PTK7452MG (PWM de 180°);
- Una fuente de alimentación para servos (5 V / ≥5 A) y un cable de datos USB-C;
- Un ordenador con el entorno de la [página 02](./02-environment.md).

## Estado verificado (2026-11-06)

Las cuatro direcciones de caída se han verificado en el robot real, cada una como una
**incorporación directa** (sin necesidad de rodar), tardando entre 1 y 6 s aproximadamente; no
se registró ninguna violación de la envolvente de los servos. El kit también incluye una
herramienta de calibración de punto cero con teclas de flecha ([página 05](./05-zero-tool.md)),
una página de estado WiFi con aprovisionamiento de red doméstica ([página 08](./08-wifi.md)) y la
simulación MuJoCo con su gemelo en vivo inalámbrico ([página 09](./09-mujoco.md)).

## Seguridad

> - Sujeta el robot en el primer encendido, mantén una zona libre de 30 cm y envía `x` o corta
>   la alimentación de los servos ante cualquier anomalía;
> - Nunca dejes un servo bloqueado más de 1 s; detente cuando la carcasa supere los 60 °C;
> - la alimentación de los servos **5 V / ≥5 A** (verificada para las cuatro direcciones de incorporación);
> - todo lo que supere 5 V va únicamente al riel de servos; **nunca** al 5V/3V3 del ESP32;
> - Todo comparte una sola masa; el orden de encendido está en la [página 04](./04-assembly.md).
