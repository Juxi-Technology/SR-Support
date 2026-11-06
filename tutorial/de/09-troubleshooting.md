---
title: 09 Fehlerbehebung
description: Häufige Symptome, Ursachen und Lösungen beim SR-Support zu IMU, serieller Schnittstelle, Fall-Gate, Ausführer-Timeouts und WLAN.
---

# 09 Fehlerbehebung

Serielle Befehle werden über einen seriellen Assistenten/Monitor gesendet: Tippen Sie sie in das
Sendefeld und drücken Sie die Eingabetaste (aktivieren Sie „send newline“ in UartAssist); serielle
Tools / der Windows-UartAssist-Download stehen auf [Seite 03, Abschnitt 3.3](./03-build-flash.md).

## 9.1 Häufige Symptome

| Symptom | Wahrscheinliche Ursache | Lösung |
|---|---|---|
| `waiting for IMU startup 5000 ms...` danach `IMU not ready` | Langsames Hochfahren der IMU, fehlerhafte Verkabelung, falsche Adresse | 5–10 s warten; 3V3, SDA=GPIO6 / SCL=GPIO7 und Adresse 0x23 prüfen |
| Wiederholtes `IMU lost -> bus reset + re-init` | Lange oder lockere I²C-Leitungen | Leitungen kürzen, Steckverbindungen neu einsetzen |
| Flashen schlägt fehl mit `could not open port` / `Access is denied` | Serielle Schnittstelle durch Monitor belegt | Zuerst `hw_monitor.py` oder den seriellen Monitor schließen |
| Roboter startet nach dem Ablegen nicht | Körper nicht ruhig, oder eine Hand berührt ihn | Loslassen und ≥0,5 s still halten; auf `getup start` achten |
| Sofortiges Umsichschlagen / falsche Richtung | Fall-Gate mitten im Rollen ausgelöst, Fehlklassifikation | Sauber ablegen und loslassen; erneut versuchen |
| Lauf stoppt und gibt nach 14 s `executor timeout` aus | Referenz nicht abgeschlossen | Normaler Fallback; automatische Wiederholung nach 1,5 s; Protokoll aufbewahren |
| Gelegentliche `executor re-plan`-Ereignisse | Normaler Fallback nach einem fehlgeschlagenen `roll_neg`-Druck | Prüfen, ob es mit `done` endet |
| Servo brummt / wird heiß | Blockieren oder klemmendes Ziel | `x` senden oder Strom unterbrechen; Grenzen und mechanischen Freiraum prüfen |
| Arm stößt bei der Selbstaufrichtung an den Körper | Große Schulterbewegung | `Q_SHOULDER_MAX` und Freiraum prüfen; Basishöhe von ~68 mm einhalten |
| `up` passt nicht zur realen Pose (anhaltende Neigung von 5°+ im Liegen) | Beschleunigungs-Nullpunkt-Offsets nicht kalibriert | Roboter waagerecht aufstellen und `c` senden (siehe [Seite 06, 6.2](./06-debug-and-calibrate.md)) |
| Arm ruht nach dem Einfahren nicht in der visuellen Mitte | Nullpunkt verschoben (neu indexiert/neu montiert ohne erneutes Nullen) | Mit dem [Werkzeug auf Seite 05](./05-zero-tool.md) neu nullen und festschreiben |
| Servo brummt/schnarrt nach einem Aufstehen | Vorübergehende Selbsterregung eines Analogservos nach großer Bewegung/Blockieren (Ausgang ist konstant) | Klingt von selbst ab; Gummilager/Dämpfungsscheiben hinzufügen oder einen Digitalservo verwenden; leichtes Kneifen des Arms bringt es sofort zum Schweigen |
| Statusseite / Einrichtung nicht erreichbar | Browser-Proxy nicht umgangen, oder Hotspot aus | `192.168.4.1` zu den Proxy-Ausnahmen hinzufügen; `w` senden, um WLAN zu aktivieren |

## 9.2 Sicherheitsbefehle

| Situation | Befehl |
|---|---|
| Bewegung sofort stoppen | `s` (letztes Ziel halten) oder `x` (PWM lösen, Drehmoment freigeben) |
| Wiederherstellen nach `x` | `r` initialisiert PWM neu und zentriert |
| Ein Gelenk bewegt sich in die falsche Richtung | `v` (Schulter) / `b` (Ellenbogen) Vorzeichenumkehr |

## 9.3 Einen Fehler festhalten

Bewahren Sie den entsprechenden Teil von `logs/hw_monitor.log` auf. Die entscheidenden Zeilen
sind:

```text
<time> getup start pose=... up=(x,y,z)
<time> executor pose=... ph=... tick=... tgt=... up=... q=... sw=...
<time> executor re-plan A -> B up=(x,y,z)
<time> standing -> executor done | executor timeout
```

---

[← Zurück zum Tutorial-Inhalt](./index.md)
