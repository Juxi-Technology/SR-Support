---
title: 08 WLAN und der Simulationszwilling
description: Statusseite, Einrichtung im Heimnetz, der drahtlose MuJoCo-Live-Zwilling und die WLAN-Telemetrie-Protokollierung.
---

# 08 WLAN und der Simulationszwilling

Dieser Schritt ist optional und für die Selbstaufrichtung selbst nicht erforderlich.

## 8.1 Hotspot und Statusseite

Hotspot: SSID `SR-Support`, Passwort `srsupport`, Adresse `192.168.4.1` (`w` schaltet ihn um; beim
Booten standardmäßig an). `w` wird über die serielle Schnittstelle gesendet: Tippen Sie `w` in das
Sendefeld des seriellen Monitors/Assistenten und drücken Sie die Eingabetaste; serielle Tools /
der Windows-UartAssist-Download stehen auf [Seite 03, Abschnitt 3.3](./03-build-flash.md).

Treten Sie dem Hotspot bei und öffnen Sie `http://192.168.4.1` (Telefone öffnen das Portal
üblicherweise automatisch). Die Seite aktualisiert sich alle 300 ms: Zustand, Hochvektor und
Aufrecht-Balken, Gelenkbefehle, Aufrichtpose/-phase, Home-WLAN-Zustand und der Schalter für den
Zwilling-Stream. Wenn der Browser einen Proxy verwendet, fügen Sie eine Ausnahme für diese
Adresse hinzu.

## 8.2 Einrichtung (dem Heim-WLAN beitreten)

Verwenden Sie auf der Statusseite die Karte „Home WiFi“: `Scan` → ein Netzwerk auswählen →
Passwort eingeben → `Connect`. Bei Erfolg läuft der ESP32 im AP+STA-Modus:

- Der Hotspot bleibt aktiv (Arbeiten am Tisch sind nicht beeinträchtigt);
- Der Roboter ist im Heim-LAN erreichbar (die Seite zeigt seine `Robot IP`);
- Die Zugangsdaten werden im NVS gespeichert und beim Booten automatisch wieder verbunden.

Nur 2,4 GHz; Scans/Verbindungen werden abgelehnt, während ein Aufrichtlauf läuft.

## 8.3 Drahtloser MuJoCo-Live-Zwilling

Drücken Sie auf der Statusseite `Twin ON` (entspricht dem seriellen `d`), dann:

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(Im Ordner `SR-Support`; erstellen und aktivieren Sie zuerst `.venv` wie auf
[Seite 02](./02-environment.md) – dort wird auch die Tool-Umgebung eingerichtet.)

- Das Fenster spiegelt die reale Lage live wider und hält den Körper auf dem Boden;
- Der Arm wird wie beim blockierten Servo in seinem Bodenkontaktwinkel gehalten (kein
  Durchdringen des Bodens);
- Das USB-Kabel wird nur zum Flashen und für Protokoll-Dumps benötigt;
- Ein aufgezeichnetes Protokoll lässt sich offline mit `--replay <file>` wiedergeben.

## 8.4 WLAN-Telemetrie-Protokollierung

```bash
python tools/tcp_log.py
```

Speichert den Telemetriestream des Hotspots in `logs/wifi_<time>.txt` zur Offline-Wiedergabe und
Analyse.

## 8.5 Simulations- und Trainingsreferenz

Das Repository enthält das MuJoCo-Modell und den Trainingscode (`training/b_line/`) zur
Wiedergabe und zum Neutraining; die Modelldateien sind auf [Seite 10](./10-reference.md)
beschrieben.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
