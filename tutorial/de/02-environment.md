---
title: 02 Umgebungseinrichtung (venv, Flash-Tools und Firmware)
description: Vor dem Start – das Projekt-.venv erstellen und aktivieren, die vorgebaute Firmware und ein offizielles Flash-Tool besorgen (Flash Download Tool / esptool), optional PlatformIO, die PC-seitigen Tools und MuJoCo sowie die serielle Schnittstelle.
---

# 02 Umgebungseinrichtung (venv, Flash-Tools und Firmware)

> Erledigen Sie diese Seite vor dem Start. **Die Befehle setzen den Repository-Stammordner
> voraus** – den **Ordner `SR-Support`**, den Sie von GitHub heruntergeladen haben (ein
> entpacktes Zip kann `SR-Support-main` heißen; es ist der Ordner, der `firmware/` und `tools/`
> enthält). **Jeder Python-Befehl läuft im Terminal mit aktiviertem `.venv`** (2.3). Das Flashen
> der vorgebauten Firmware erfordert kein PlatformIO und keine Kompilierung; die
> Entwicklerumgebung (2.5) dient nur zum Ändern des Codes.

## 2.1 Anforderungen

- Windows, Linux oder macOS (jeder Befehl unten ist dort, wo es darauf ankommt, für alle drei angegeben);
- ein USB-**Daten**kabel (ein reines Ladekabel lässt das Board nicht erscheinen);
- ESP32-S3-DevKitC-1 (8 MB Flash).

## 2.2 Code und vorgebaute Firmware besorgen

- Klonen Sie das Repository (oder entpacken Sie das mitgelieferte Archiv) und führen Sie spätere
  Befehle aus dem **Repository-Stammordner** aus:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (Das Repository ist privat – fordern Sie zuerst Zugriff an.)

- Das **vorgebaute Image** liegt in `firmware/releases/`:

  | Datei | Zweck |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | Hauptfirmware (bei 0x0 flashen; wird auch zur Zentrierung bei der Montage verwendet: bis zum Firmware-Nullpunkt einschalten, `e` optional) |
  | `SHA256SUMS` | Prüfsummen |

## 2.3 Virtuelle Umgebung erstellen und aktivieren (.venv)

Alle PC-seitigen Python-Tools (esptool, PlatformIO, die MuJoCo-Tools) gehören in **dasselbe**
projektlokale `.venv`, und dieses `.venv` muss im **Ordner `SR-Support`** erstellt werden, den
Sie von GitHub heruntergeladen haben (ein entpacktes Zip kann `SR-Support-main` heißen; auch hier
gilt: der Ordner, der `firmware/` und `tools/` enthält).

Wechseln Sie zuerst in diesen Ordner – die folgenden Befehle laufen dort:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Nicht sicher, ob Sie am richtigen Ort sind? Führen Sie `dir` aus; es muss `firmware`, `tools`,
  `tutorial` auflisten;
- Ohne Python 3.12 verwenden Sie `py -3 -m venv .venv` (3.10+ funktioniert);
- Wenn PowerShell die Ausführung von Skripten verweigert, führen Sie
  `Set-ExecutionPolicy -Scope Process Bypass` in diesem Fenster aus und aktivieren Sie erneut;
- `.\.venv\Scripts\Activate.ps1` ist das **PowerShell-Aktivierungsskript**, das venv erzeugt:
  Das führende `.\` bedeutet „das Skript im aktuellen Ordner ausführen“ und ist in PowerShell
  erforderlich (ein einfaches `Activate.ps1` wird nicht gefunden). Andere Shells verwenden ihre
  eigene Datei:
  - **cmd.exe**: `.venv\Scripts\activate.bat`
  - **Git Bash**: `source .venv/Scripts/activate`
  - Das venv verlassen Sie mit `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> So unterscheiden Sie die Shells: cmd-Prompts sehen aus wie `C:\...>`, PowerShell wie
> `PS C:\...>`. Das Tutorial verwendet standardmäßig PowerShell; in cmd tauschen Sie einfach den
> Aktivierungsbefehl gegen `activate.bat`, alles andere ist identisch. Administratorrechte sind
> nicht nötig.
>
> **Die Aktivierungsdatei muss zur Shell passen**: cmd verwendet `activate.bat`, PowerShell
> verwendet `Activate.ps1`. Das Ausführen der `.ps1` aus cmd heraus aktiviert nicht das aktuelle
> Fenster (meist passiert nichts, oder es öffnet sich ein separates Fenster). Stellen Sie außerdem
> sicher, dass `.venv` zuerst existiert (`dir` muss den Ordner `.venv` auflisten); falls nicht,
> führen Sie zuerst `py -3.12 -m venv .venv` aus.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- Nicht sicher, ob Sie am richtigen Ort sind? Führen Sie `ls` aus; es muss `firmware`, `tools`,
  `tutorial` auflisten.

Nach der Aktivierung zeigt der Prompt **`(.venv)`**. Jeder Befehl unten und auf den späteren
Tutorial-Seiten läuft in diesem **aktivierten Terminal**; aktivieren Sie nach dem Öffnen eines
neuen Fensters erneut. Ohne Aktivierung verweisen `pip` / `python` auf die Systeminstallation,
und Installationen oder Aufrufe schlagen fehl.

Bestätigen Sie, dass die Aktivierung funktioniert hat:

- Windows: `where python` – die erste Zeile muss `...\SR-Support\.venv\Scripts\python.exe` sein;
- Linux / macOS: `which python` – muss `.../SR-Support/.venv/bin/python` sein.

> **Bildschirm nach dem Aktivieren in cmd geleert?** Das mitgelieferte `activate.bat` schaltet
> vorübergehend die Konsolen-Codepage um (`chcp 65001`), und manche Terminals zeichnen den
> Bildschirm neu – es ist **kein neues Terminal**. Wenn der neue Prompt mit `(.venv)` beginnt und
> `where python` in `.venv` zeigt, war die Aktivierung erfolgreich. Um den Neuaufbau zu vermeiden,
> verwenden Sie Powershells `Activate.ps1` (es berührt die Codepage nicht) oder rufen Sie
> `.venv\Scripts\python.exe` ohne Aktivierung auf.

> **Verzeichnisanforderung (wichtig)**: `.venv` muss im **Ordner `SR-Support` (dem
> Repository-Stammordner)** liegen, niemals in einem Unterordner. Die Erstellungs-/Aktivierungsbefehle
> oben verwenden **relative Pfade** und müssen daher aus diesem Ordner ausgeführt werden – wechseln
> Sie nach dem Öffnen eines neuen Terminals zuerst dorthin (PowerShell: `cd D:\Project\SR-Support`;
> cmd: `cd /d D:\Project\SR-Support`, mit Ihrem Pfad), bevor Sie aktivieren, oder verwenden Sie einen
> absoluten Pfad wie `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Nach der Aktivierung können Sie in jeden beliebigen Unterordner `cd`en, und `python` / `pip` /
> `pio` zeigen weiterhin auf dieses `.venv`; die Pfade `tools/...`, `firmware/...` und
> `hardware/v1/...` des Tutorials sind jedoch relativ, also **führen Sie sie aus dem Ordner
> `SR-Support` aus**. Das venv ist an den Pfad gebunden, an dem es erstellt wurde: Nach dem
> Verschieben oder Umbenennen des Repositorys löschen Sie `.venv` und erstellen es neu.

## 2.4 Flash-Tools (alle Kunden – eines wählen)

Ein vorgebautes Image ist eine einzelne Binärdatei, die bei 0x0 geflasht wird – **kein
PlatformIO, kein Toolchain-Download**. Stellen Sie sicher, dass das Terminal im Ordner
`SR-Support` ist und der Prompt `(.venv)` zeigt.

**A. Windows-GUI: Espressif Flash Download Tool**

1. Öffnen Sie die offizielle „Other Tools“-Seite von Espressif und laden Sie die Flash Download
   Tools herunter: <https://www.espressif.com/en/support/download/other-tools>
2. Starten Sie es; wählen Sie **ESP32-S3**, laden Sie
   `firmware/releases/sr_support_b_ptk_factory.bin` unter der Adresse `0x0`, wählen Sie den Port
   und klicken Sie auf **START**.

> Das Flash Download Tool gibt es nur für Windows; unter Linux/macOS verwenden Sie unten esptool.

**B. Windows / Linux / macOS: esptool (Kommandozeile)**

```bash
pip install esptool
```

Langsames Netzwerk in China – verwenden Sie einen Mirror:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Flashen (`COM27` ist Ihr Port; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

Wenn die Verbindung fehlschlägt, wechseln Sie in den Download-Modus: **BOOT** halten, **RST**
antippen, **BOOT** loslassen.

## 2.5 PlatformIO (nur Entwickler – Build aus dem Quellcode)

> Überspringen Sie dies, außer Sie ändern den Code. **Hinweis**: PlatformIO (einschließlich der
> PlatformIO-Erweiterung für VS Code) lädt bei der ersten Verwendung die espressif32-Plattform und
> die Xtensa-Toolchain herunter (~1 GB von der PlatformIO-Registry und GitHub). In vielen Netzen
> in China ist das langsam oder schlägt fehl und erfordert einen Proxy/VPN; die VS-Code-Erweiterung
> vermeidet den Download nicht.

Mit dem Terminal im Ordner `SR-Support` und aktivem `(.venv)`:

```bash
pip install platformio
```

Unter Windows können Sie auch `tools/install_platformio.ps1` ausführen, das in dasselbe `.venv`
installiert. Prüfen Sie:

```bash
pio --version
```

> Ältere Tutorial-Versionen installierten PlatformIO in ein separates `.venv-pio`; jetzt liegt es
> im einzigen `.venv`. Wenn `pio` nach dem Upgrade nicht gefunden wird, führen Sie
> `pip install platformio` im aktivierten `.venv` aus (oder starten Sie
> `tools/install_platformio.ps1` erneut); das alte `.venv-pio` kann gelöscht werden.

## 2.6 PC-seitige Tools und MuJoCo-Umgebung (Zwilling / Nullpunkt / Protokolle)

Für das Flashen nicht erforderlich. Installieren Sie dies, wenn Sie das Nullpunkt-Werkzeug mit
Pfeiltasten, den MuJoCo-Live-Zwilling (`tools/live_twin.py`), die Simulationswiedergabe oder die
Protokoll-Tools verwenden. Installieren Sie mit dem Terminal im Ordner `SR-Support` und aktivem
`.venv` die Abhängigkeiten (pyserial, numpy, MuJoCo 3.1+, gymnasium):

```bash
pip install -r tools/requirements.txt
```

Unter Windows können Sie auch `tools/install_tools_env.ps1` ausführen (erstellt/verwendet `.venv`
wieder und installiert denselben Satz). Bei langsamem Netzwerk in China hängen Sie den
Tsinghua-Mirror `-i https://pypi.tuna.tsinghua.edu.cn/simple` an; die erste Installation lädt
einige hundert MB herunter.

**Prüfen: Führen Sie den Umgebungs-Selbsttest aus (er lädt MuJoCo und führt Schritte aus, nicht nur Importe)**

```bash
python tools/env_check.py
```

Die letzte Zeile muss `env check: PASS` sein, mit einer Ausgabe wie:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Ohne angeschlossenes Board ist `[--] no serial port found` informativ und beeinträchtigt PASS nicht.

> Unter Linux bedeutet ein GLFW/OpenGL-Fehler beim Öffnen des MuJoCo-Fensters, dass
> Systembibliotheken fehlen: Installieren Sie `libgl1` und `libglew-dev` (z. B.
> `sudo apt install libgl1 libglew-dev`). Die MuJoCo-Wheels für Windows/macOS enthalten alles
> Nötige. Die Simulation `training/b_line` und die Wiedergabe verwenden dieselbe Umgebung – nichts
> Zusätzliches zu installieren.

## 2.7 Board anschließen und serielle Schnittstelle bestätigen

1. Schließen Sie das Board über USB-C an; unter Windows lesen Sie die COM-Nummer im Geräte-Manager
   ab, unter Linux ist es üblicherweise `/dev/ttyACM0` (fügen Sie Ihren Benutzer der Gruppe
   `dialout` hinzu), unter macOS üblicherweise `/dev/tty.usbmodem*`;
2. Merken Sie sich den Port – jedes `COM27` auf späteren Seiten ist dieser Wert;
3. Ein serieller Monitor oder `hw_monitor.py` belegt den Port; schließen Sie ihn vor dem Flashen.

## 2.8 Checkliste

- [ ] Das Terminal befindet sich im **Repository-Stammordner** und der Prompt zeigt `(.venv)`
      (prüfen mit `pwd` / `Get-Location`);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` existiert und verifiziert
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` funktioniert, oder das Flash Download Tool öffnet sich;
- [ ] Die serielle Schnittstelle des Boards ist sichtbar;
- [ ] (Entwickler) `pio --version` funktioniert;
- [ ] `python tools/env_check.py` gibt `env check: PASS` aus.

Fahren Sie erst fort, wenn die benötigten Punkte erfüllt sind.

---

[← Zurück zum Tutorial-Inhalt](./index.md)
