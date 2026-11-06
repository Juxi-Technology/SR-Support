---
title: 03 Hauptfirmware flashen
description: Die SR-Support-B-Line-Firmware aus der vorgebauten Binärdatei flashen (Flash Download Tool / esptool) oder mit PlatformIO bauen; serielle Befehle und Boot-Protokoll.
---

# 03 Hauptfirmware flashen

> **Nutzer eines fertigen Geräts können diese Seite überspringen**: Das Werk hat die Firmware
> geflasht und verifiziert. Wiederholen Sie dies nur bei Firmware-Upgrades oder nach Änderungen
> am Code. Kunden verwenden das vorgebaute Image (3.1, kein PlatformIO); Entwickler bauen aus
> dem Quellcode (3.2).

## 3.1 Vorgebautes Image flashen (für Kunden empfohlen)

1. Stellen Sie sicher, dass Sie `firmware/releases/sr_support_b_ptk_factory.bin` haben
   (Prüfsummen in der danebenliegenden `SHA256SUMS`);
2. Wechseln Sie in den Download-Modus: **BOOT** halten, **RST** antippen, **BOOT** loslassen;
3. Flashen Sie (Tool-Einrichtung auf [Seite 02, Abschnitt 2.4](./02-environment.md); führen Sie
   diese Befehle im Ordner `SR-Support` mit aktiviertem `.venv` aus):
   - Windows-GUI: Flash Download Tool → ESP32-S3 → die Binärdatei bei `0x0` laden → START;
   - Windows / Linux / macOS Kommandozeile:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. Drücken Sie danach RST und lesen Sie das Protokoll wie in 3.3.

> Zum Flashen / seriellen Debuggen können Sie den ESP32 über USB versorgen und das 5-V-Netzteil
> nur für die Servos belassen (die beiden Stromversorgungsoptionen stehen in
> [Seite 04, Abschnitt 4.4](./04-assembly.md)).

> Der Befehl ist **auf Windows / Linux / macOS identisch**; nur der Port ändert sich:
> `COM27` unter Windows, `/dev/ttyACM0` unter Linux, `/dev/tty.usbmodem*` unter macOS.
> Das Flash Download Tool gibt es nur für Windows; verwenden Sie andernorts die
> esptool-Kommandozeile.

> Die Zentrierung bei der Montage benötigt kein zweites Image: Nach dem Flashen dieses Images
> schalten Sie ein – beide Servos fahren auf den Firmware-Nullpunkt (1681 / 1456 µs) –, schalten
> dann aus und montieren die Servohörner ([Seite 04, Abschnitt 4.2](./04-assembly.md)). Optional
> senden Sie zuerst `e`, um sie auf die elektrische Mitte von 1520 µs zu bringen (gleichwertig).

## 3.2 Aus dem Quellcode bauen und flashen (Entwickler)

Umgebung: [Seite 02, Abschnitt 2.5](./02-environment.md). Projekt:
`firmware/sr_support_b_ptk/` (Umgebung `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Führen Sie diese im Ordner `SR-Support` mit aktiviertem `.venv` aus (Seite 02, Abschnitt 2.3);
> sie sind auf allen drei Plattformen identisch – ersetzen Sie `COM27` in `--upload-port` durch
> Ihren Port. Schließen Sie alles, was die serielle Schnittstelle belegt (serieller Monitor,
> `tools/hw_monitor.py`), bevor Sie flashen, sonst erhalten Sie `could not open port` /
> `Access is denied`.

Ein erfolgreicher Build belegt etwa 56 % RAM und 30 % Flash (WLAN + Webserver enthalten;
frühere Builds ohne WLAN lagen bei etwa 7 % / 12 %).

## 3.3 Serieller Monitor

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Auf allen drei Plattformen gleich; ersetzen Sie `COM27` durch Ihren Port.)

> **Serieller Windows-GUI-Assistent (optional)**: UartAssist von 野人家园 (kostenlos, einzelne
> exe, nur Windows). Offizielle Seite <https://cmsoft.cn/resource/101.html>, offizieller
> Download-Einstieg <https://cmsoft.cn/resource/download/101>. Wählen Sie den COM-Port,
> **115200, 8N1, keine Flusskontrolle**, aktivieren Sie „send newline“; beobachten Sie das
> Boot-Protokoll/die Telemetrie im Empfangsbereich und tippen Sie Befehle in das Sendefeld.
> Laden Sie es nur über den offiziellen Link herunter (Drittanbieter-Seiten bündeln oft Adware);
> committen Sie die exe nicht in dieses Repository.

**Serielle Betrachter für Linux / macOS (einen wählen)**:

- Bevorzugt: der Befehl `pio device monitor` oben (mit dem Projekt installiert, plattformübergreifend);
- Leichtgewichtige CLI: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` unter macOS; Beenden mit `Ctrl-]`); das eingebaute
  `screen /dev/ttyACM0 115200` funktioniert ebenfalls (Beenden mit `Ctrl-A`, dann `K`);
- GUI: **CoolTerm** (kostenlos, Windows/macOS/Linux, offizielle Seite
  <https://freeware.the-meiers.org>); unter Linux können Sie auch `sudo apt install cutecom`
  ausführen.

> Fügen Sie unter Linux Ihren Benutzer der Gruppe `dialout` hinzu:
> `sudo usermod -aG dialout $USER`, dann melden Sie sich ab und wieder an.

Nach dem Öffnen des Ports sehen Sie zuerst das Boot-Protokoll, wenn das Board gerade eingeschaltet
wurde oder Sie RST gedrückt haben; falls nicht, drücken Sie einmal RST. Nach dem Reset sollten Sie
Folgendes sehen:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Serielle Befehle (115200)

Tippen Sie jeden Befehl in das **Sendefeld** des seriellen Monitors/Assistenten und drücken Sie
die Eingabetaste (aktivieren Sie „send newline“ in UartAssist); der Befehl `m` benötigt ein
Leerzeichen und zwei Werte, z. B. `m 0.5 0`.

| Befehl | Funktion |
|---|---|
| `g` | Ausführung starten/fortsetzen (dieser Build startet automatisch; meist nicht nötig) |
| `s` | Ausführer stoppen, letztes Ziel halten |
| `x` | Notfreigabe: PWM lösen; mit `r` wieder scharfschalten |
| `r` | PWM neu initialisieren und zentrieren |
| `t` | Servo-Selbsttest (kleine Bewegung) |
| `c` | Gyroskop + **Beschleunigungs-Nullpunkt-Offsets** kalibrieren (Roboter muss GERADE und ruhig STEHEN; wird im NVS gespeichert) |
| `m <q1> <q2>` | Manuelle Gelenkziele in rad |
| `1/2` | Manuelle Schulter ±0,5 rad |
| `3/4` | Manueller Ellenbogen ±0,5 rad |
| `0` | Manuelle Neutralstellung |
| `l` | 3 s schnelles Protokoll mit 50 Hz |
| `k` | Mitten-Pulsweiten beider Servos ausgeben |
| `o` / `p` | Schulter-Mitte um ±10 µs trimmen |
| `z` | Nullpunkt nach Encoder-Art: die aktuelle Pose wird für beide Gelenke zu q=0; gibt die neuen Pulsweiten aus (nur im RAM; siehe [Seite 05](./05-zero-tool.md)) |
| `e` | Elektrische Mitte (optional): beide Servos auf 1520 µs, um die Servohörner in der elektrischen Mitte zu montieren; üblich ist, bis zum Firmware-Nullpunkt einzuschalten und dort zu montieren (siehe [Seite 04, 4.2](./04-assembly.md)) |
| `d` | Den 50-Hz-Zwilling-Stream umschalten (MuJoCo-Zwilling; derselbe Schalter auf der Statusseite) |
| `w` | WLAN umschalten (Hotspot + Statusseite/Einrichtung, siehe [Seite 08](./08-wifi-twin.md)) |
| `v` / `b` | Vorzeichen von Schulter / Ellenbogen umkehren |
| `i` / `j` | Vorzeichen der IMU X / Y umkehren |
| `h` | Stand-Homing-Umschaltung (Legacy-Richtlinienpfad) |
| `a` | Legacy-Testmodus für skriptgesteuertes Aufstehen |

## 3.5 Verhalten beim Einschalten

Die Firmware definiert `AUTORUN_ON_BOOT`: Nach dem Einschalten wartet der Ausführer, bis der
Roboter **vollständig am Boden und ruhig** ist, 0,5 s lang, und startet dann automatisch – kein
`g` nötig. Schalten Sie den Roboter aufrecht ein.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
