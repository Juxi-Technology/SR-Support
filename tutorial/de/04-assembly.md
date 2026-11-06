---
title: 04 Montage: Drucken, Bauen, Verkabeln
description: Drucken, Neuindexierung und Zentrierung der Servohörner, Verkabelungstabelle, Einbaulage der IMU und Einschaltreihenfolge für SR-Support.
---

# 04 Montage: Drucken, Bauen, Verkabeln

> **Nutzer eines fertigen Geräts können diese Seite überspringen**: Das Werk hat das Gerät
> bereits gedruckt, montiert, verkabelt und geprüft (siehe den Abschnitt zum Werkszustand in
> [index](./index.md)). Befolgen Sie diese Seite nur beim Bau aus Einzelteilen oder beim Austausch
> von Komponenten.

## 4.1 Drucken und Prüfen

1. Drucken Sie Grundplatte, Schulter-Servohalterung, Ellenbogen-Servohalterung und obere Strebe (je 1);
2. Prüfen Sie den Umriss der Basis (~88 × 82 mm) und die Gesamthöhe (~68 mm) mit dem Messschieber;
3. Probieren Sie die 25T-Servohörner in ihren Aufnahmen; fixieren Sie sie nur dann mit Schrauben,
   wenn nichts klemmt;
4. Wiegen Sie jedes gedruckte Teil und tragen Sie das Gewicht gegen
   `hardware/v1/meshes/print_mass_model.json` ein.

## 4.2 Servovorbereitung (Firmware-Nullpunkt und Montage der Servohörner)

1. **Zuerst verkabeln und flashen**: Verkabeln Sie beide Servos, die IMU, die Servostromversorgung
   und die gemeinsame Masse gemäß der Tabelle in 4.4 (mechanische Teile noch nicht montiert; die
   Hauptfirmware benötigt die IMU zum Booten), und flashen Sie dann die Hauptfirmware gemäß
   [Seite 03, Abschnitt 3.1](./03-build-flash.md);
2. **Zum Firmware-Nullpunkt einschalten**: Öffnen Sie die serielle Schnittstelle mit 115200
   (serielle Tools / der UartAssist-Download stehen auf [Seite 03, Abschnitt 3.3](./03-build-flash.md))
   und schalten Sie ein; nach dem Booten fährt die Firmware beide Servos auf q=0 (Mittenpulse
   1681 / 1456 µs). Wenn das Protokoll `servo start q: 0.00 0.00 rad` und
   `ready; send g to run` (oder `autorun on: ...`) zeigt, stehen die Servos auf dem Nullpunkt;
3. **Ausschalten**: Unterbrechen Sie die Servostromversorgung (USB darf angeschlossen bleiben) und
   stellen Sie sicher, dass beide Servos entlastet sind;
4. **Servohörner montieren**: Montieren Sie das Schulterhorn so, dass der Oberarm senkrecht steht,
   und das Ellenbogenhorn so, dass der Unterarm mit ihm fluchtet; ziehen Sie die Schrauben fest und
   prüfen Sie den gesamten Verfahrweg von Hand;
5. Richtungskonvention (entspricht dem Simulator): `shoulder +q` bewegt den großen Arm in
   Richtung **−Y**, `elbow +q` bewegt den Unterarm in Richtung **+X**; die Firmware-Vorgaben sind
   `SERVO_SHOULDER_SIGN=-1`, `SERVO_ELBOW_SIGN=-1`.

> Die Firmware-Mitten von 1681 / 1456 µs enthalten bereits die Servohorn-Neuindexierung aus der
> Werkskalibrierung – **zählen Sie keine Zähne**: Montieren Sie die Servohörner am
> Firmware-Nullpunkt mit senkrechtem Arm. Alternativ (gleichwertig, optional) tippen Sie `e` in
> das serielle Sendefeld und drücken Sie die Eingabetaste, um beide Servos auf die elektrische
> Mitte von 1520 µs zu bringen und dort zu montieren (siehe Befehlstabelle auf
> [Seite 03](./03-build-flash.md)); in beiden Fällen erledigt der Befehl `z` von
> [Seite 05](./05-zero-tool.md) den abschließenden präzisen Nullpunkt.

> Die Montage am Firmware-Nullpunkt ist nur eine **grobe Zentrierung** (die Servohorn-Verzahnung
> ist diskret). Der präzise Nullpunkt muss nach vollständiger Montage und dem Flashen der
> Hauptfirmware ([Seite 03](./03-build-flash.md)) mit dem [Nullpunkt-Werkzeug auf Seite 05](./05-zero-tool.md)
> gesetzt werden: die visuell senkrechte Pose als q=0 erklären (`z` verwendet die IMU nicht und
> funktioniert in jeder Pose), dann die ausgegebenen Pulsweiten in `config.h` festschreiben und
> neu flashen. Selbst wenn das Servohorn nicht perfekt montiert wurde, korrigiert diese
> Nullpunkt-Kalibrierung das; nur wenn auf einer Seite der Verfahrweg fehlt (die Pulsweite bei
> 500/2500 µs anschlägt), müssen Sie das Servohorn abziehen und neu indexieren. Die
> Horneinstellung legt fest, wie sich der Verfahrweg auf die beiden Seiten verteilt; die manuellen
> Firmware-Grenzen (`Q_SHOULDER_MIN/MAX`) müssen zum realen Verfahrweg passen – erweitern Sie sie
> nicht. Verschieben Sie nach der Nullpunkt-Kalibrierung alle Sequenz-Wegpunkte wie auf Seite 05
> beschrieben, sonst driften die physischen Aufrichtposen.

## 4.3 Montage von Basis und Arm

1. Verbinden Sie die Grundplatte und die Schulter-Servohalterung mit M3-Schrauben zur Basis
   (~68 mm hoch);
2. Setzen Sie den Schulter-Servo in die Schulterhalterung ein, das Servohorn nach oben;
3. Befestigen Sie die Ellenbogen-Servohalterung am Schulterhorn und ziehen Sie sie fest (sie bildet
   den Oberarm); setzen Sie den Ellenbogen-Servo in die Ellenbogenhalterung ein;
4. Verbinden Sie die obere Strebe (Unterarm) mit dem Ellenbogenhorn;
5. Bringen Sie den Arm von Hand in die Senkrechte (`q≈0`) und bestätigen Sie, dass dies der
   Servomitte entspricht.

## 4.4 Verkabelung

| Gerät | ESP32-S3-Pin | Adapter | Hinweise |
|---|---|---|---|
| Adapter 3V3 | 3V3 | S1-Signalpin | anderes Ende an IMU VCC (3,3 V) |
| Schulter-Signal | GPIO4 | S4 | 50 Hz PWM |
| Ellenbogen-Signal | GPIO5 | S5 | 50 Hz PWM |
| IMU SDA | GPIO6 | S6-Signalpin | anderes Ende an IMU SDA; I²C 0x23, 100 kHz |
| IMU SCL | GPIO7 | S7-Signalpin | anderes Ende an IMU SCL; I²C 0x23, 100 kHz |
| IMU GND | GND | — (direkt) | gemeinsame Masse |
| LED (optional) | GPIO2 | — | Status-LED |
| 5-V-Stromeingang | 5V / GND | — | 1-auf-2-Kabel: ein Zweig zum ESP32, einer zum Adapter V+/GND für die Servos |
| Servostromversorgung | — | V+/GND-Klemme | 5 V / ≥5 A; **höhere Spannungen nur über diese Klemme, niemals über den ESP32 5V** |
| S2 / S3 | — | — | nicht angeschlossen |

Hinweise:

- Der Adapter ist ein passiver Durchschleifer: S1/S6/S7 führen 3V3 / SDA / SCL auf ihren
  Signalpins, S4/S5 führen die Servosignale; prüfen Sie die Reihenfolge V+/GND/Signal an jeder
  Stiftleiste – verpolte Spannung zerstört Servos oder das Board;
- Halten Sie I²C-Leitungen kurz und fern von Servoleitungen; die Pull-ups des Moduls liegen auf 3,3 V;
- Bei einer **5-V**-Versorgung dürfen Sie den ESP32 5V/GND speisen und denselben Versorgungskreis
  zum Adapter V+/GND für die Servos abzweigen; höhere Spannungen (6 V / 7,4 V) dürfen nur den
  Adapter V+/GND speisen, und der ESP32 muss über USB versorgt werden;
- **Bei einem 5-V-Akku, der den ESP32 speist, darf das Type-C-Kabel eingesteckt bleiben**: Im
  offiziellen DevKitC-1-Schaltplan erreicht jedes USB-VBUS über eine Schottky-Diode das 5V-Netz,
  sodass keine Rückspeisung erfolgt und USB als Datenverbindung (plus Zusatzstromversorgung)
  funktioniert. Bei einem Clone-Board ohne diese Diode, oder wenn Sie sie nicht bestätigen können,
  ziehen Sie beim Flashen den 5-V-Zweig zum ESP32 ab und versorgen ihn über USB (Option 2);
- **Stromversorgung beim Debuggen / Flashen (beides ist normal; eines wählen)**:
  1. Das 5-V-Netzteil versorgt ESP32 und Servos über den Verteiler, USB überträgt nur Daten;
  2. leichter nachzuvollziehen: Ziehen Sie den 5-V-Zweig zum ESP32 ab, versorgen Sie den ESP32
     allein über USB und lassen Sie das 5-V-Netzteil nur die Servos speisen.
  Verwenden Sie Option 2 zum Flashen, für die serielle Überwachung und die Kalibrierung mit `c`;
  Option 1 für den eigenständigen Betrieb;
- Lassen Sie bei der ersten Inbetriebnahme die Servos abgeklemmt, prüfen Sie V+-Polarität und
  -Spannung mit einem Multimeter und testen Sie dann einen Servo, danach beide;
- Verkabelungsreihenfolge: Masse und Signale → 5-V-Versorgung (ESP32 und Servos gemeinsam) → USB
  für die serielle Schnittstelle bei Bedarf. Beim Ausschalten umgekehrt.

## 4.5 Einbaulage der IMU

Die IMU wird mit Schrauben an der Basis fixiert (ihre Ausrichtung ist nicht verstellbar), daher
aktiviert die Firmware `IMU_YAW90` und rechnet den Hochvektor aus dem IMU-Koordinatensystem in
Körperkoordinaten um:

```c
up_body = (up_imu.y, -up_imu.x, up_imu.z)
```

**Mechanische Orientierungsprüfung** (möglich, sobald die Servos montiert sind, vor dem
Einschalten): Anhand der auf dem IMU-Modul aufgedruckten / dokumentierten Achsen

- zeigt die **Servo-Abtriebswelle** des Schulter-Servos (die Welle, auf der das Servohorn sitzt;
  auch Hornwelle oder Getriebewelle genannt) zur IMU **−Y**;
- zeigt die Servo-Abtriebswelle des Ellenbogen-Servos zur IMU **+X**.

Von unten nach oben sind die beiden Servos **Schulter (unten) → Ellenbogen (oben)**; vertauschen
Sie sie beim Montieren der Servohörner oder beim Verkabeln nicht.

Diese beiden Richtungen sind die Schulter- und Ellenbogenachse des Körpers; wenn sie nicht zur
Hardware passen, ist die IMU oder eine Servohalterung falsch eingebaut – beheben Sie das vor dem
Einschalten.

Prüfen Sie es nach dem Einschalten erneut auf [Seite 06](./06-debug-and-calibrate.md): aufrecht
ergibt `up≈(0, 0, 1)`; die vier Liegeposen sind in der Tabelle in 6.5 aufgeführt.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
