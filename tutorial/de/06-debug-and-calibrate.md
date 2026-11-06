---
title: 06 Debug und Kalibrierung
description: Telemetrieformat, IMU- und Servoprüfungen, Gyro- und Beschleunigungskalibrierung, Mittenprüfung, vier Liegeposen und das Fall-Gate, Abschlusskriterien.
---

# 06 Debug und Kalibrierung

> **Nutzer eines fertigen Geräts können diese Seite überspringen**: Das Werk kalibriert und
> verifiziert jedes Gerät. Wiederholen Sie diese Schritte nur nach dem Austausch eines
> Servos/der IMU, nach erneuter Servohorn-Montage oder wenn der Verdacht besteht, dass ein
> Firmware-Upgrade die Kalibrierung gestört hat.

Dies ist die **funktionale Prüfung und Kalibrierung des gesamten Roboters** nach Montage,
Flashen und Nullpunkt-Kalibrierung; arbeiten Sie sie der Reihe nach durch, bevor Sie den Roboter
verwenden.

> **Stromversorgung beim Debuggen**: USB überträgt nur serielle Daten. `c` benötigt nur die IMU
> (die Servos dürfen unversorgt bleiben); `t` / `z` / `e` benötigen die 5-V-Servoschiene. Wenn
> Sie den ESP32 nicht aus zwei Quellen speisen wollen, ziehen Sie den 5-V-Zweig zum ESP32 ab,
> versorgen ihn allein über USB und lassen das 5-V-Netzteil nur die Servos speisen – ein normaler
> Aufbau, siehe [Seite 04, Abschnitt 4.4](./04-assembly.md).

## 6.1 Serielle Schnittstelle öffnen und Telemetrie lesen

Öffnen Sie im Ordner `SR-Support` mit aktiviertem `.venv` die serielle Schnittstelle (`COM27` ist
Ihr Port):

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Serielle Tools / der Windows-UartAssist-Download stehen auf
[Seite 03, Abschnitt 3.3](./03-build-flash.md).)

Nach dem Öffnen des Ports sehen Sie zuerst das Boot-Protokoll, wenn das Board gerade eingeschaltet
wurde oder Sie RST gedrückt haben; falls kein Boot-Protokoll erscheint, drücken Sie einmal RST.
Danach folgt alle 250 ms eine Telemetriezeile:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Feld | Bedeutung | Ablesung |
|---|---|---|
| `up` | Welt-Hochvektor in Körperkoordinaten (x vorwärts, y links, z oben) | aufrecht `(0,0,1)`, Neigung≈0°; Liegeposen in 6.5 (z. B. `(-1,0,0)`=pitch_pos) |
| `w` | Winkelgeschwindigkeit (rad/s) | ≈0 in Ruhe; ungleich null beim Aufstehen/Abrollen; das Fall-Gate benötigt `|w|<0.9` |
| `q` | Aktuelle Gelenk-**Befehlswinkel** (Schulter, Ellenbogen, rad; keine Rückmeldung) | q=0 ist Arm senkrecht; Schulter + → großer Arm in Richtung −Y, Ellenbogen + → Unterarm in Richtung +X |
| `qd` | Gelenk-Befehlsraten | selten benötigt |
| `mode` | Laufmodus | `run` / `hold` / `manual` / `auto` |

Beispielwerte (Fenster von `hw_watch`):

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

`tilt` ist der Winkel zwischen dem Hochvektor und der Senkrechten (aus `up_z`); 0° bedeutet
vollständig aufrecht.

Wenn der scrollende Strom schwer zu lesen ist, verwenden Sie das Live-Fenster mit fester Zeile
(die Befehle funktionieren weiterhin):

```bash
python tools/hw_watch.py --port COM27
```

Es zeichnet up/Neigung, Winkelgeschwindigkeit, Gelenkwinkel, Modus und das letzte Ereignis an Ort
und Stelle neu; tippen Sie bei `cmd>` und drücken Sie die Eingabetaste, um einen Befehl zu senden,
und Ereignisse werden zusätzlich an `logs/hw_watch.log` angehängt. Für einen vollständigen
Aufrichtlauf, bei dem jede Rohzeile zählt, verwenden Sie weiterhin `pio device monitor` oder
`tools/hw_monitor.py` (letzteres schreibt alle 5 s eine Zusammenfassung ins Protokoll).

**So senden Sie serielle Befehle**: Lassen Sie den Monitor geöffnet und tippen Sie den Befehl
gefolgt von der Eingabetaste (Ein-Zeichen-Befehle brauchen keine Anführungszeichen). Auf dieser
Seite verwendete Befehle:

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

Die vollständige Befehlstabelle steht auf [Seite 03, Abschnitt 3.4](./03-build-flash.md).

**Kurzes Selbstprüfskript** (schließen Sie zuerst den seriellen Monitor, damit der Port frei ist):

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

Der erste Befehl liest 0,6 s Telemetrie; bei `--tilt 8` neigen Sie den Roboter von Hand, und es
gibt die Bereiche für up/Gyro sowie den Neigungsbereich aus, was eine blockierte oder falsch
orientierte IMU aufdeckt.

## 6.2 IMU-Prüfungen und Kalibrierung

`c` bewirkt zwei Dinge:

1. **Gyroskop-Nullpunkt-Bias**: mittelt 200 Ruheproben (etwa 2 s) zum Nullraten-Offset; dieser
   gilt für den aktuellen Einschaltzyklus und wird bei jedem Booten automatisch neu bestimmt;
2. **Beschleunigungs-Nullpunkt**: aus denselben Proben wird der Gravitationsvektor gemittelt;
   dazu muss der Roboter waagerecht stehen (Gravitation vollständig auf +Z), die Firmware prüft
   ihn auf Plausibilität und speichert ihn im NVS (wird beim Booten geladen).

Vorgehen (Servostromversorgung nicht erforderlich):

1. Führen Sie zuerst die mechanische Orientierungsprüfung auf
   [Seite 04, Abschnitt 4.5](./04-assembly.md) durch (Schulterwelle zur IMU −Y, Ellenbogenwelle
   zur IMU +X);
2. Stellen Sie den Roboter aufrecht auf einen WASSERWAAGERECHTEN Tisch, lassen Sie ihn los, Kabel
   dürfen nicht ziehen;
3. Tippen Sie `c` und drücken Sie die Eingabetaste im seriellen Monitor oder bei `cmd>` von
   `hw_watch`:

   ```text
   c
   ```

4. Halten Sie etwa 2 s still; bei Erfolg wird ausgegeben:

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

5. `accel cal rejected: |a|=...` bedeutet, dass der Roboter nicht waagerecht oder nicht ruhig
   stand (die Gravitationsnorm weicht mehr als 1,5 m/s² von 9,8 ab); der Bias bleibt unverändert –
   stellen Sie ihn erneut auf und senden Sie `c` noch einmal.

Überprüfung:

- Neigen Sie langsam nach links/rechts und vor/zurück: Die x/y-Komponenten von `up` müssen
  flüssig folgen; wenn eine Richtung vertauscht ist, senden Sie `i` / `j`, um das Vorzeichen der
  IMU-Achse umzukehren, und führen Sie `c` erneut aus;
- Legen Sie den Roboter ab und warten Sie 2 s: `up` muss mit der Liegeposen-Tabelle in 6.5
  übereinstimmen (z. B. `(0,-1,0)` = roll_neg), wobei die Basisfläche flach aufliegt;
- Eine anhaltende Neigung von 5°+ im Liegen bedeutet meist, dass der Beschleunigungs-Nullpunkt
  falsch ist – wiederholen Sie diesen Abschnitt.

> Fertige Geräte sind im Werk kalibriert (im NVS gespeichert); wiederholen Sie dies nur nach dem
> Austausch/erneuter Montage der IMU oder wenn die Liegepose sichtbar geneigt ist. `c` kalibriert
> nur die IMU – es ändert nicht den Servo-Nullpunkt (das ist [Seite 05](./05-zero-tool.md)).
>
> Wenn Sie vor der Kalibrierung manuelle Befehle verwendet haben (die Telemetrie endet auf
> `manual`), lässt `c` den Roboter in `hold`/`manual`, und das Fall-Gate startet kein Aufstehen;
> halten Sie ihn aufrecht und senden Sie `g` zum Fortsetzen, oder setzen Sie das Board zurück.

## 6.3 Servoprüfungen und Richtungs-Selbsttest

| Prüfung | Methode | Erwartet |
|---|---|---|
| Mitten | `k` | `centers: shoulder 1681 us, elbow 1456 us` (Werte der visuellen Mitte, eingebrannt 2026-11; neu nullen gemäß [Seite 05](./05-zero-tool.md)) |
| Schulter-Trim | `o` / `p` (±10 µs) | Arm senkrecht bei `q=0` |
| Richtung | `m 0.5 0` / `m 0 0.5` | Schulter + → großer Arm in Richtung −Y; Ellenbogen + → Unterarm in Richtung +X |
| Vorzeichenumkehr | `v` (Schulter) / `b` (Ellenbogen) | Nur wenn eine Richtung vertauscht ist |
| Selbsttest | `t` | Kleine Bewegung an beiden Gelenken, dann Mitte |
| Neutral | `m 0 0` oder `r` | Arm senkrecht |

Gelenkgrenzen:

- Manuelle Schulterbefehle `[-1.85, +1.82]` rad; Ellenbogen mechanisch `±1.55` rad (vom Ausführer
  erreichbar);
- Manuelle `m`-Befehle begrenzen den Ellenbogen auf `[-0.90, +0.70]` rad;
- PWM-Ausgang 500–2500 µs bei 50 Hz.

Tippen Sie diese nacheinander in das **Sendefeld** des seriellen Monitors/Assistenten (nach jedem
die Eingabetaste):

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Bestätigen Sie: Schulter `q>0` → großer Arm in Richtung **−Y**; Ellenbogen `q>0` → Unterarm in
Richtung **+X**. Falsche Richtung: mit `v` / `b` umkehren oder das Servohorn neu montieren.

## 6.4 Mittenprüfung

Im Werk eingebrannt (Schulter 1681 µs / Ellenbogen 1456 µs) – **bei einem Seriengerät
überspringbar**. In einem DIY-Bau wurde dies bereits mit der
[Nullpunkt-Kalibrierung auf Seite 05](./05-zero-tool.md) erledigt und die Werte in `config.h`
festgeschrieben (neu flashen, falls sie sich geändert haben); führen Sie hier nur `k` aus, um zu
bestätigen, dass die Mitten mit den eingebrannten Werten übereinstimmen. Kehren Sie nur nach dem
Neuindexieren eines Servohorns, erneuter Montage oder wenn der Arm nicht mehr in der visuellen
Mitte ruht, zu Seite 05 zurück.

## 6.5 Vier Liegeposen und das Fall-Gate

| Pose | Monitor-`up` | Physische Bedeutung |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | Die Oberseite des Körpers zeigt in Richtung +X |
| `pitch_neg` | `(+1, 0, 0)` | Die Oberseite des Körpers zeigt in Richtung −X |
| `roll_pos` | `(0, +1, 0)` | Die Oberseite des Körpers zeigt in Richtung −Y |
| `roll_neg` | `(0, -1, 0)` | Die Oberseite des Körpers zeigt in Richtung +Y |

Fall-Gate-Bedingung (Firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Erst dann gibt sie `getup start pose=...` aus und beginnt. Legen Sie den Roboter also ab, lassen
Sie ihn los und halten Sie ihn ~0,5 s still; wenn Sie ihn direkt nach dem Ablegen hin und her
bewegen, berührt ihn meist noch eine Hand, oder der Körper rollt noch.

Prüfung: Legen Sie den Roboter in jede der vier Posen, lassen Sie los und halten Sie ihn still;
innerhalb von 0,5 s muss das serielle Protokoll `getup start pose=<matching pose>` zeigen.

## 6.6 Abschlusskriterien

- [ ] `c` gibt `accel bias ... (saved)` aus;
- [ ] `t` zeigt an beiden Gelenken die korrekten Richtungen;
- [ ] `k` entspricht den eingebrannten Mitten (oder Sie haben gemäß Seite 05 neu genullt und dies
      festgeschrieben);
- [ ] alle vier Liegeposen lösen `getup start` aus.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
