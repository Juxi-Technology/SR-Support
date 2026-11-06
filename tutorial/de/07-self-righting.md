---
title: 07 Selbstaufrichtung: Anwendung und Überwachung
description: Bedienung des SR-Support in jeder Liegerichtung, erwartete Bewegungszeiten, serielle Ereignisse und Überwachungsprotokolle.
---

# 07 Selbstaufrichtung: Anwendung und Überwachung

> Jedes fertige Gerät wird vor dem Versand in allen vier Richtungen getestet. Prüfen Sie bei der
> ersten Verwendung dennoch jede Richtung einmal gemäß Abschnitt 7.2, um sicherzustellen, dass
> das Gerät den Transport unbeschadet überstanden hat.

## 7.1 Ablauf

1. Schalten Sie den Roboter aufrecht ein und warten Sie auf `autorun on: get-up waits for a fall`;
2. Stoßen Sie den Roboter in eine beliebige Richtung um, **lassen Sie ihn los und halten Sie ihn
   etwa 0,5 s still**;
3. Wenn `getup start pose=<pose>` erscheint, startet der Ausführer automatisch;
4. Bei Erfolg gibt die Firmware `standing -> executor done` aus und kehrt in den Bereitschaftszustand
   zurück;
5. Wenn ein Lauf 14 s überschreitet, gibt die Firmware `executor timeout` aus; nach einer
   Abklingzeit von 1,5 s löst das Fall-Gate erneut aus und wiederholt den Versuch.

## 7.2 Erwartetes Verhalten je Richtung

| Pose | Mechanismus | Zeit am realen Roboter |
|---|---|---|
| `pitch_neg` (Oberseite → −X) | Ellenbogen setzt auf, Schulterhub hebelt den Körper hoch | ~3 s |
| `pitch_pos` (Oberseite → +X) | Derselbe Hub; wenn er beim Einfahren umkippt, führt die Posen-Neuplanung `pitch_pos` erneut aus | ~5–6 s |
| `roll_pos` (Oberseite → −Y) | Direkter Schulterhebel über die Seite mit dem langen Verfahrweg | ~3 s |
| `roll_neg` (Oberseite → +Y) | **Direkter Druck über den vollen Verfahrweg → Ellenbogen-Keilpumpen ×2 → bei Bedarf Whip-Slam-Wiederholung**; kein Überrollen | ~2–6 s |

> Frühere Firmware rollte `roll_neg` über die Oberseite und plante auf einen Pitch-Hub um
> (5–14 s); der aktuelle Build verwendet das Spiegelbild des +Y-Drucks, sodass alle vier
> Richtungen symmetrisch und in der Geschwindigkeit vergleichbar sind. Ein gelegentliches
> `executor re-plan roll_neg -> ...` bedeutet nur, dass dieser Druck fehlgeschlagen ist und die
> Fallback-Wiederholung gegriffen hat – das ist das normale Sicherheitsnetz.

## 7.3 Ausführer-Logik (in der Firmware)

- 20 Ticks (0,4 s) pro Referenzwegpunkt, lineare Interpolation; Stellratenbegrenzung des Ausgangs
  0,08 rad/Tick;
- Nach den Wegpunkten den Arm mit 0,033 rad/Tick auf Neutral zurückfahren;
- Fertig, wenn `up_z > 0.95` bei Ziel null für 50 Ticks;
- Wenn sich der Körper auf einer anderen Liegeachse beruhigt (`up_z<0.6`, `|ω|<0.8` für 15
  Ticks), auf Neutral zurückfahren und auf die Referenz der neuen Pose umschalten (bis zu 5
  Umschaltungen);
- Die `roll_neg`-Referenz verwendet **stufenweise adaptive Haltezeiten**: Druck-/Pumpstufen
  halten, solange `up_z<0.92`, bis zu einer Tick-Obergrenze pro Stufe (Druck 40 / Pumpe 30 /
  Pumpe 30 / Whip 40 / Finale 90); kommt der Körper mitten in der Sequenz aufrecht, springt der
  Ausführer direkt zum Einfahren, damit die späteren Stufen den stehenden Roboter nicht umstoßen
  können.

## 7.4 Überwachung und Protokolle

```bash
python tools/hw_monitor.py COM27
```

(Führen Sie es im Ordner `SR-Support` mit aktiviertem `.venv` aus – [Seite 02](./02-environment.md).
Schließen Sie zuerst jeden seriellen Assistenten/Monitor; serielle Tools / der Windows-UartAssist-
Download stehen auf [Seite 03, Abschnitt 3.3](./03-build-flash.md).)

- Hängt Ereignisse und Telemetrie-Zusammenfassungen im 5-Sekunden-Takt an `logs/hw_monitor.log` an;
- Zeichnet `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost` usw. auf;
- Prüft die Servo-Grenzwerte (Schulter `[-1.85,+1.82]`, Ellenbogen `±1.55`) und schreibt
  `!! VIOLATION`;
- Während der Ausführer läuft, gibt es alle 0,2 s einen Trace aus:

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Feld | Bedeutung |
|---|---|
| `pose` | Aktuelle Referenzpose |
| `ph` / `tick` | Wegpunktphase / Tick innerhalb der Phase |
| `tgt` | Ziel-Gelenkwinkel |
| `up` | Aktueller Hochvektor |
| `q` | Aktueller Gelenkbefehl |
| `sw` | Bisherige Anzahl der Posenumschaltungen |

> Das Öffnen des Monitors setzt den ESP32 zurück; schließen Sie ihn vor dem Flashen.

## 7.5 Dokumentation

Notieren Sie für jeden Test die Pose, ob er mit `done` endete, die Dauer, die Anzahl der
Umschaltungen und etwaige Verletzungen der Grenzwerte. `logs/hw_monitor.log` ist der maßgebliche
Datensatz.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
