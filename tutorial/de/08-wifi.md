---
title: 08 WLAN-Statusseite und Einrichtung im Heimnetz
description: Hotspot, Statusseite und Einrichtung im Heimnetz; die MuJoCo-Simulation und der Live-Zwilling werden auf Seite 09 behandelt.
---

# 08 WLAN-Statusseite und Einrichtung im Heimnetz

Dieser Schritt ist optional und für die Selbstaufrichtung selbst nicht erforderlich. Das
MuJoCo-Simulationsfenster und der Live-Zwilling haben ihre eigene Seite:
[Seite 09](./09-mujoco.md).

## 8.1 Hotspot und Statusseite

Hotspot: SSID `SR-Support`, Passwort `srsupport`, Adresse `192.168.4.1` (`w` schaltet ihn um; beim
Booten standardmäßig an). `w` wird über die serielle Schnittstelle gesendet: Tippen Sie `w` in das
Sendefeld des seriellen Monitors/Assistenten und drücken Sie die Eingabetaste; serielle Tools /
der Windows-UartAssist-Download stehen auf [Seite 03, Abschnitt 3.3](./03-build-flash.md).

Treten Sie dem Hotspot bei und öffnen Sie `http://192.168.4.1` (Telefone öffnen das Portal
üblicherweise automatisch). Die Seite aktualisiert sich alle 300 ms: Zustand, Hochvektor und
Aufrecht-Balken, Gelenkbefehle, Aufrichtpose/-phase, Home-WLAN-Zustand und der Schalter für den
Zwilling-Stream (Live-Spiegelung auf [Seite 09](./09-mujoco.md)). Wenn der Browser einen Proxy
verwendet, fügen Sie eine Ausnahme für diese Adresse hinzu.

![Abbildung 8-1 Die Statusseite des Roboters](../images/sr-support/wifi/01-status-page.png)

*Abbildung 8-1: die Statusseite des Roboters (im Browser unter der Roboteradresse geöffnet). Hier ist der Roboter dem Heimnetz beigetreten: Die Home-WiFi-Karte zeigt Verbindungsstatus und die Robot IP, darunter der Twin-Stream-Schalter (Verwendung in 9.2).*

## 8.2 Einrichtung (dem Heim-WLAN beitreten)

Verwenden Sie auf der Statusseite die Karte „Home WiFi“: `Scan` → ein Netzwerk auswählen →
Passwort eingeben → `Connect`. Bei Erfolg läuft der ESP32 im AP+STA-Modus:

- Der Hotspot bleibt aktiv (Arbeiten am Tisch sind nicht beeinträchtigt);
- Der Roboter ist im Heim-LAN erreichbar (die Seite zeigt seine `Robot IP` - diese Adresse im Zwillings-Befehl auf Seite 09 verwenden);
- Die Zugangsdaten werden im NVS gespeichert und beim Booten automatisch wieder verbunden.

Nur 2,4 GHz; Scans/Verbindungen werden abgelehnt, während ein Aufrichtlauf läuft.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
