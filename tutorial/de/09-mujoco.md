---
title: 09 MuJoCo-Simulation und der Live-Zwilling
description: Das lokale MuJoCo-Simulationsfenster (Aufricht-Wiedergabe in vier Posen), der WLAN-Live-Zwilling des realen Roboters und die Telemetrie-Protokollierung.
---

# 09 MuJoCo-Simulation und der Live-Zwilling

MuJoCo wird in diesem Projekt auf zwei Arten eingesetzt, beide mit `hardware/v1/robot_v1.xml`
(dem quellgleichen Modell des realen Roboters):

- **Lokale Simulation**: ohne angeschlossenen Roboter die vier Liegeposen und ihre
  Aufrichtvorgänge auf dem Computer in einer Schleife abspielen, um die Referenzsequenzen zu
  validieren und die Bewegung zu beobachten;
- **Live-Zwilling**: der reale Roboter streamt seine Lage über WLAN und das MuJoCo-Fenster
  spiegelt die reale Bewegung in Echtzeit wider (ein digitaler Zwilling).

Das Fenster funktioniert in beiden Fällen gleich: Ziehen mit der linken Maustaste dreht die
Ansicht, Ziehen mit der rechten Maustaste verschiebt sie, und das Mausrad zoomt. Erstellen und
aktivieren Sie vor der ersten Verwendung die `.venv` wie auf [Seite 02](./02-environment.md) und
installieren Sie darin die Tool-Abhängigkeiten (`pip install -r tools/requirements.txt`, siehe
Seite 02).

## 9.1 Lokales Simulationsfenster

Im Ordner `SR-Support` (`.venv` aktiviert):

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

Das Fenster trägt den Titel `MuJoCo : sr_support_v1` (Abbildung 9-1). Der Roboter wird der Reihe
nach in die vier Liegeposen gesetzt (`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`); jedes
Mal führt der Ausführer die Referenzsequenz mit exakt den Firmware-Parametern aus, bis der
Roboter steht, dann wird die nächste Pose gesetzt. Die Schleife wiederholt sich, bis Sie das
Fenster schließen. Das Terminal gibt die Pose und das Ergebnis aus:

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` bedeutet, dass die Pose in der Simulation aufgestanden ist. Bei `ok=False` prüfen Sie
die Referenzsequenz und alle von Ihnen geänderten Parameter anhand von
[Seite 06](./06-debug-and-calibrate.md).

![Abbildung 9-1 Das MuJoCo-Simulationsfenster (Aufricht-Wiedergabe in vier Posen)](../images/sr-support/mujoco/01-mujoco-window.png)

*Abbildung 9-1: ein Frame aus der Vier-Posen-Schleife - der Ausführer richtet gerade eine Liegepose auf.*

> Bekannte Modellabweichung: Mit dem 1×-Masse-Modell gibt `roll_neg` in der Simulation
> `ok=False` aus (Armmasse/Reibung des Modells weichen vom realen Roboter ab, siehe
> [Seite 11](./11-reference.md) 11.4); die reale Firmware ist davon nicht betroffen.

## 9.2 Live-Zwilling über WLAN

Voraussetzung: Der Roboter ist wie auf [Seite 08](./08-wifi.md) dem Heimnetz beigetreten und
der Computer ist im selben Netz. Die Statusseite zeigt die Adresse des Roboters als `Robot IP`;
kopieren Sie sie in den folgenden Befehl.

1. Drücken Sie auf der Statusseite `Twin ON` (entspricht dem seriellen `d`);
2. Führen Sie im Ordner `SR-Support` mit aktiviertem `.venv` aus (Adresse durch die `Robot IP`
   der Statusseite ersetzen):

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

Das Modell spiegelt die reale Lage live wider (50-Hz-Quaternion-Stream) und hält den Körper auf
dem Boden; der Arm wird wie beim blockierten Servo in seinem Bodenkontaktwinkel gehalten, sodass
er nie in den Boden eindringt.

- Computer direkt am Hotspot des Roboters: Die Adresse ist immer `192.168.4.1`,
  `python tools/live_twin.py --tcp 192.168.4.1:3333`;
- Kabelgebundene Alternative: `python tools/live_twin.py --port COM27` (das Tool sendet `d`, um
  den Stream automatisch zu aktivieren);
- Offline-Wiedergabe: `python tools/live_twin.py --replay logs/hw_fast_xxx.txt`;
- Der Zwilling ist bis auf das Umschalten des Streams schreibgeschützt: Er sendet nie
  Steuerbefehle.

## 9.3 Telemetrie-Protokollierung

```bash
python tools/tcp_log.py
```

Speichert den Telemetriestream in `logs/wifi_<time>.txt` für die Offline-Wiedergabe
(`--replay`) und die Fehleranalyse. Am Hotspot verbindet es sich standardmäßig mit
`192.168.4.1:3333`; im Heimnetz übergeben Sie die `Robot IP` der Statusseite:

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 Simulations- und Trainingsreferenz

`training/b_line/` enthält den Ausführer, die Referenzsequenzen und die Simulationsumgebung –
wertgleich mit der Firmware – für Wiedergabe, Validierung und Parametertuning; die Modelldateien
sind auf [Seite 11](./11-reference.md) 11.1 beschrieben.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
