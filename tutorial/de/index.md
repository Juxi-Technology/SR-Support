---
title: SR-Support Selbstaufrichtender Roboter – Tutorial
description: Vollständiges Tutorial für das SR-Support-2-DOF-Selbstaufrichtungsgerät, von den Grundlagen und der Umgebungseinrichtung über Flashen, Montage, Nullpunkt und Kalibrierung bis hin zur Selbstaufrichtungsanwendung und Fehlerbehebung.
---

# SR-Support Selbstaufrichtender Roboter – Tutorial

[简体中文](../zh-hans/index.md) · [繁體中文](../zh-hant/index.md) · [English](../en/index.md) · [日本語](../ja/index.md) · [한국어](../ko/index.md) · [Deutsch](../de/index.md) · [Français](../fr/index.md) · [Español](../es/index.md) · [Italiano](../it/index.md) · [Português (BR)](../pt-br/index.md) · [Português (PT)](../pt-pt/index.md)


SR-Support ist ein kostengünstiges aktives Selbstaufrichtungsgerät auf Basis eines 2-DOF-Arms.
Nach dem Umkippen in eine beliebige Richtung setzt es seinen zweigelenkigen Arm auf dem Boden ab,
rollt ab und hebelt sich wieder in die aufrechte Position. Dieses Tutorial ist als Lesereihenfolge
organisiert und deckt den gesamten Weg von Null bis zum verifizierten Aufbau ab.

## Lesereihenfolge

| # | Seite | Inhalt | Hinweis |
|---|---|---|---|
| 01 | [Grundlagen](./01-basics.md) | Funktionsprinzip, Spezifikationen, Stückliste | zuerst lesen |
| 02 | [Umgebungseinrichtung](./02-environment.md) | `.venv` erstellen/aktivieren, vorgebaute Firmware + Flash-Tools (Flash Download Tool / esptool), PC-seitige Tools und MuJoCo-Umgebung, optional PlatformIO, serielle Schnittstelle | **zuerst erledigen** |
| 03 | [Hauptfirmware flashen](./03-build-flash.md) | Vorgebaute Binärdatei (für Kunden empfohlen) oder Quellcode-Build mit PlatformIO, serielle Befehle, Bootverhalten | bei Seriengeräten überspringbar |
| 04 | [Montage: Drucken, Bauen, Verkabeln](./04-assembly.md) | Gedruckte Teile, Servohorn-Index, Verkabelungstabelle, IMU-Montage | bei Seriengeräten überspringbar |
| 05 | [Nullpunkt-Kalibrierung](./05-zero-tool.md) | Joggen mit Pfeiltasten + Nullpunkt setzen mit `z` (nach Neuindexierung/Neumontage) | **für DIY-Bauten erforderlich**; bei Seriengeräten überspringbar |
| 06 | [Debug und Kalibrierung](./06-debug-and-calibrate.md) | Prüfung und Kalibrierung des gesamten Roboters: Telemetrie, IMU, Servos, Mittenprüfung, vier Liegepositionen, Fall-Gate | |
| 07 | [Selbstaufrichtung: Anwendung und Überwachung](./07-self-righting.md) | Vier Fallrichtungen, erwartete Bewegung, Überwachung und Protokolle | |
| 08 | [WLAN und der Simulationszwilling](./08-wifi-twin.md) | Statusseite, Einrichtung im Heim-WLAN, drahtloser MuJoCo-Zwilling | optional |
| 09 | [Fehlerbehebung](./09-troubleshooting.md) | Häufige Symptome und Lösungen | Referenz |
| 10 | [Referenz: Modell, Parameter, Lizenzierung](./10-reference.md) | Modelldateien (XML/STL), Parameter, Referenzsequenzen, Lizenzierung | Referenz |

## Werkszustand eines fertigen Geräts (zwei Lesepfade)

Dieses Tutorial bedient zwei Zielgruppen – wählen Sie den Pfad, der zu Ihnen passt:

| Leser | Werkszustand | Empfohlener Pfad |
|---|---|---|
| **Nutzer eines fertigen Geräts** | Montiert und verkabelt, Firmware geflasht, **kalibriert** (Servo-Nullpunkte und IMU-Beschleunigungs-Nullpunkte fest eingebrannt), **getestet** (alle vier Aufrichtrichtungen pro Gerät verifiziert) | Direkt zu [07 Anwendung](./07-self-righting.md) und [08 WLAN/Zwilling](./08-wifi-twin.md) (optional); [09](./09-troubleshooting.md)/[10](./10-reference.md) als Referenz behalten. **Die Seiten 02/03/04/05/06 werden nur bei Firmware-Upgrades, Servo-/IMU-Austausch oder erneuter Servohorn-Montage benötigt**; um die Zwilling-/Telemetrie-Tools von Seite 08 zu nutzen, installieren Sie zuerst die PC-seitigen Tools von Seite 02. |
| **Kit- / DIY-Bauer** | Beginnt bei den Einzelteilen | Folgen Sie [01](./01-basics.md) → [02](./02-environment.md) → [03 Flashen](./03-build-flash.md) → [04 Montage](./04-assembly.md) → [05 Nullpunkt (erforderlich)](./05-zero-tool.md) → [06 Debug/Kalibrierung](./06-debug-and-calibrate.md) → [07](./07-self-righting.md) vollständig von Anfang bis Ende. Sowohl die Nullpunkt-Kalibrierung (05) als auch die Kalibrierung (06) erfolgen **nach vollständiger Montage und dem Flashen**: `z` verwendet die IMU nicht und funktioniert in jeder Pose; `c` erfordert den montierten, aufrecht stehenden Roboter. |

> Empfohlene Erstinbetriebnahme-Prüfung für ein fertiges Gerät: aufrecht einschalten → `up≈(0,0,1)` bestätigen →
> es einmal in jede der vier Richtungen gemäß [Seite 07](./07-self-righting.md) kippen und
> bestätigen, dass es aufsteht.

## Voraussetzungen

- Mechanische Teile des SR-Support (Grundplatte, Schulter-Servohalterung, Ellenbogen-Servohalterung, obere Strebe; Druck und Montage auf [Seite 04](./04-assembly.md));
- ESP32-S3-Board, Juxi ICM42670P IMU, passive Direct-Drive-Servo-Adapterplatine;
- 2× PTK7452MG (180° PWM) Servos;
- Ein Servo-Netzteil (5 V / ≥5 A) und ein USB-C-Datenkabel;
- Ein Computer mit der Umgebung aus [Seite 02](./02-environment.md).

## Verifizierter Stand (2026-11-06)

Alle vier Liegerichtungen wurden am realen Roboter verifiziert, jeweils als **direktes Aufstehen**
(kein Überrollen nötig), mit etwa 1–6 s Dauer; es wurden keine Verletzungen der Servo-Grenzwerte
aufgezeichnet. Das Kit enthält außerdem ein Nullpunkt-Kalibrierwerkzeug mit Pfeiltasten
([Seite 05](./05-zero-tool.md)), eine WLAN-Statusseite mit Einrichtung im Heimnetz und einen
drahtlosen MuJoCo-Live-Zwilling ([Seite 08](./08-wifi-twin.md)).

## Sicherheit

> - Halten Sie den Roboter bei der ersten Inbetriebnahme fest, halten Sie 30 cm Freiraum ein und
>   senden Sie bei jeder Anomalie `x` oder unterbrechen Sie die Servostromversorgung;
> - Blockieren Sie einen Servo nie länger als 1 s; stoppen Sie, wenn das Gehäuse 60 °C überschreitet;
> - die Servoversorgung **5 V / ≥5 A** (verifiziert für alle vier Aufrichtrichtungen);
> - alles über 5 V geht ausschließlich auf die Servoschiene – **niemals** an den ESP32 5V/3V3;
> - Alles teilt sich eine Masse; die Einschaltreihenfolge steht in [Seite 04](./04-assembly.md).
