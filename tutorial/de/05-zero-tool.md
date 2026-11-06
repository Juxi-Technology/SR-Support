---
title: 05 Nullpunkt-Kalibrierung (Pfeiltasten; erforderlich für DIY-Bauten)
description: Den Arm mit den Pfeiltasten zur visuellen Mitte verfahren und diese als q=0 festlegen; erforderlich für jeden DIY-Bau sowie nach dem Neuindexieren eines Servohorns oder erneuter Montage.
---

# 05 Nullpunkt-Kalibrierung (Pfeiltasten; erforderlich für DIY-Bauten)

Die Servo-Nullpunkte und die IMU-Beschleunigungs-Nullpunkte werden im Werk pro Gerät kalibriert
und fest eingebrannt, daher braucht ein Seriengerät hier nichts. Ein **DIY-Bau muss diese Seite
erledigen**: Ein von Hand montierter Arm sitzt fast nie exakt in der Mitte. Selbst wenn das
Servohorn nicht genau am Firmware-Nullpunkt montiert wurde, können Sie das hier korrigieren –
verfahren Sie den Arm mit den Pfeiltasten visuell in die Senkrechte und drücken Sie `z`, um die
**aktuelle** Pose als q=0 zu erklären. Der Befehl `z` verwendet die IMU nicht und funktioniert in
jeder Pose und bei jeder Servohorn-Stellung.

Kommen Sie hierher zurück, wenn: ein Servohorn neu indexiert wurde, der Arm zerlegt/neu montiert
wurde, ein Servo ersetzt wurde, die IMU ersetzt/neu montiert wurde (Beschleunigung neu
kalibrieren) oder der Arm nach dem Einfahren nicht mehr in der visuellen Mitte ruht.

> `z` verschiebt nur den Software-Nullpunkt; es ändert **nicht**, wie die Servohorn-Stellung den
> Verfahrweg aufteilt (PWM 500–2500 µs). Wenn nach der Nullpunkt-Kalibrierung eine Richtung an
> die Grenze stößt (die Pulsweite bei 500/2500 µs anschlägt und der Arm einen erforderlichen
> Sequenzwinkel nicht erreicht), indexieren Sie das Servohorn neu (an der Schulter etwa 2 Zähne)
> und kalibrieren Sie erneut.

Zeitpunkt: nachdem der Roboter vollständig montiert und die Hauptfirmware geflasht ist (der
DIY-Pfad läuft 03 → 04 → 05).

## 5.1 Prinzip

Die Firmware definiert q=0 als visuelle Mitte: Arm senkrecht, beide Glieder in einer Linie. Der
Befehl `z` ist ein Nullpunkt nach Encoder-Art: Er macht die **aktuellen** Gelenkpositionen zu q=0
und gibt die entsprechenden Mitten-Pulsweiten aus.

## 5.2 Ablauf

1. Schließen Sie Akku und USB an (Servos mit Strom versorgt) und führen Sie dies im Ordner
   `SR-Support` mit aktiviertem `.venv` aus:

   ```bash
   python tools/hw_shoulder_range.py
   ```

   Schließen Sie zuerst jeden seriellen Assistenten/Monitor (er belegt den Port); die Tasten im
   Fenster unten liest dieses Tool, ein serieller Assistent ist nicht nötig. Serielle Tools / der
   Windows-UartAssist-Download stehen auf [Seite 03, Abschnitt 3.3](./03-build-flash.md).

   Eine dauerhafte vierteilige Anzeige aktualisiert sich an Ort und Stelle:

   ```
   Up/Dn=BigArm  L/R=SmallArm  Sh:fast
   z=SetCenter  k=Read  n=Home  q=Quit
   SmallArm: +0.000 rad (  +0 deg)
   BigArm:   +0.000 rad (  +0 deg)
   ```

2. Verfahren Sie mit den Pfeiltasten: `↑`/`↓` = großer Arm ±0,05 rad, `←`/`→` = kleiner Arm
   ±0,05 rad (Umschalt = ±0,20), bis der Arm **senkrecht und ausgerichtet** aussieht;
3. Drücken Sie `z`; die Firmware gibt aus:

   ```text
   zero set: shoulder XXXX us, elbow XXXX us (current pose is now q = 0)
   ```

4. Plausibilitätsprüfung: Drücken Sie `n` (Home), verfahren Sie ein Stück, wieder Home – der Arm
   muss in die gerade definierte visuelle Mitte zurückkehren.

## 5.3 Festschreiben (nach Zufriedenheit zwingend erforderlich)

`z` verändert nur den RAM; ein Neustart stellt den alten Nullpunkt wieder her. Wenn alles passt:

1. Schreiben Sie die beiden Pulsweiten in `config.h`
   (`SERVO_SHOULDER_CENTER_US` / `SERVO_CENTER_US`);
2. Verschieben Sie jeden Wegpunkt von `EXEC_REF*` und `training/b_line/getup_reference_b39.py` um
   dieselben Offsets (Schulter/Ellenbogen jeweils −Δ rad);
3. Flashen Sie neu und testen Sie alle vier Richtungen erneut ([Seite 07](./07-self-righting.md)).

> Ein Fehlgriff ist harmlos: einfach erneut nullen, um zu überschreiben.

## 5.4 Verwandte Befehle

| Befehl | Funktion |
|---|---|
| `z` | Die aktuelle Pose wird für beide Gelenke zu q=0; gibt die neuen Mittenpulse aus (nur im RAM) |
| `k` | Die aktuellen Mittenpulse ausgeben (Schulter/Ellenbogen, µs) |
| `o` / `p` | Schulter-Mitte live um ±10 µs trimmen (wird beim Neustart zurückgesetzt) |

---

[← Zurück zum Tutorial-Inhalt](./index.md)
