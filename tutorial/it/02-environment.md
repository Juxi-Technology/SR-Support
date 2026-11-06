---
title: 02 Preparazione dell'ambiente (venv, strumenti di flash e firmware)
description: Prima di iniziare - crea e attiva il file .venv del progetto, procurati il firmware precompilato e uno strumento di flash ufficiale (Flash Download Tool / esptool), PlatformIO opzionale, gli strumenti lato computer e MuJoCo, e la porta seriale.
---

# 02 Preparazione dell'ambiente (venv, strumenti di flash e firmware)

> Completa questa pagina prima di iniziare. **I comandi presuppongono la radice del
> repository** - la **cartella `SR-Support`** scaricata da GitHub (un archivio zip estratto può
> chiamarsi `SR-Support-main`; è la cartella che contiene `firmware/` e `tools/`). **Ogni
> comando Python va eseguito nel terminale con `.venv` attivato** (2.3). Il flash del firmware
> precompilato non richiede PlatformIO né compilazione; l'ambiente per sviluppatori (2.5) serve
> solo per modificare il codice.

## 2.1 Requisiti

- Windows, Linux o macOS (ogni comando seguente è riportato per tutti e tre dove rilevante);
- un cavo USB **dati** (un cavo di sola ricarica non enumera la scheda);
- ESP32-S3-DevKitC-1 (8 MB di flash).

## 2.2 Ottenere il codice e il firmware precompilato

- Clona il repository (o decomprimi l'archivio fornito) ed esegui i comandi successivi dalla
  **radice del repository**:

  ```bash
  git clone https://github.com/Juxi-Technology/SR-Support.git
  cd SR-Support
  ```

  (Il repository è privato: richiedi prima l'accesso.)

- L'**immagine precompilata** si trova in `firmware/releases/`:

  | File | Scopo |
  |---|---|
  | `sr_support_b_ptk_factory.bin` | firmware principale (flash a 0x0; usato anche per la centratura in assemblaggio: accendi fino allo zero del firmware, `e` opzionale) |
  | `SHA256SUMS` | somme di controllo |

## 2.3 Creare e attivare l'ambiente virtuale (.venv)

Tutti gli strumenti Python lato computer (esptool, PlatformIO, gli strumenti MuJoCo) vanno nella
**stessa** `.venv` locale del progetto, e tale `.venv` deve essere creata dentro la **cartella
`SR-Support`** scaricata da GitHub (un archivio zip estratto può chiamarsi `SR-Support-main`;
di nuovo, la cartella che contiene `firmware/` e `tools/`).

Entra prima in quella cartella: i comandi seguenti vanno eseguiti lì:

**Windows (PowerShell)**

```powershell
cd D:\Project\SR-Support    # replace with where your SR-Support folder lives
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Non sei sicuro di essere nel posto giusto? Esegui `dir`; deve elencare `firmware`, `tools`, `tutorial`;
- senza Python 3.12, usa `py -3 -m venv .venv` (va bene dalla 3.10 in su);
- se PowerShell rifiuta di eseguire script, esegui
  `Set-ExecutionPolicy -Scope Process Bypass` in questa finestra e riattiva;
- `.\.venv\Scripts\Activate.ps1` è lo **script di attivazione per PowerShell** creato da venv:
  il `.\` iniziale significa "esegui lo script nella cartella corrente" ed è obbligatorio in
  PowerShell (il semplice `Activate.ps1` non verrà trovato). Le altre shell usano il proprio file:
  - **cmd.exe**: `.venv\Scripts\activate.bat`
  - **Git Bash**: `source .venv/Scripts/activate`
  - Per uscire dalla venv: `deactivate`

**Windows (cmd.exe)**

```bat
cd /d D:\Project\SR-Support    # cmd needs /d to change drive; plain cd D:\... stays on C:
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

> Come distinguere le shell: il prompt di cmd è simile a `C:\...>`, quello di PowerShell a
> `PS C:\...>`. Il tutorial usa PowerShell per impostazione predefinita; in cmd basta sostituire
> il comando di attivazione con `activate.bat`, il resto è identico. Non servono privilegi di
> amministratore.
>
> **Il file di attivazione deve corrispondere alla shell**: cmd usa `activate.bat`, PowerShell
> usa `Activate.ps1`. Eseguire il `.ps1` da cmd non attiva la finestra corrente (di solito non
> succede nulla, oppure si apre una finestra separata). Assicurati anche che `.venv` esista già
> (`dir` deve elencare la cartella `.venv`); altrimenti esegui prima `py -3.12 -m venv .venv`.

**Linux / macOS**

```bash
cd ~/SR-Support             # replace with where your SR-Support folder lives
python3 -m venv .venv
source .venv/bin/activate
```

- Non sei sicuro di essere nel posto giusto? Esegui `ls`; deve elencare `firmware`, `tools`, `tutorial`.

Dopo l'attivazione il prompt mostra **`(.venv)`**. Ogni comando seguente e nelle pagine
successive del tutorial va eseguito in questo **terminale attivato**; riattiva dopo aver aperto
una nuova finestra. Senza attivazione `pip` / `python` puntano all'installazione di sistema e le
installazioni o le esecuzioni falliranno.

Conferma che l'attivazione abbia funzionato:

- Windows: `where python` - la prima riga deve essere `...\SR-Support\.venv\Scripts\python.exe`;
- Linux / macOS: `which python` - deve essere `.../SR-Support/.venv/bin/python`.

> **Schermo ripulito dopo l'attivazione in cmd?** Il file `activate.bat` standard cambia
> temporaneamente la code page della console (`chcp 65001`) e alcuni terminali ridisegnano lo
> schermo: **non è un nuovo terminale**. Se il nuovo prompt inizia con `(.venv)` e `where python`
> punta dentro `.venv`, l'attivazione è riuscita. Per evitare il ridisegno, usa `Activate.ps1`
> di PowerShell (non tocca la code page) oppure richiama `.venv\Scripts\python.exe` senza attivare.

> **Requisito sulla cartella (importante)**: `.venv` deve trovarsi nella **cartella `SR-Support`
> (la radice del repository)**, mai in una sottocartella. I comandi di creazione/attivazione
> sopra usano **percorsi relativi**, quindi vanno eseguiti da quella cartella - dopo aver aperto
> un nuovo terminale, entraci (PowerShell: `cd D:\Project\SR-Support`; cmd:
> `cd /d D:\Project\SR-Support`, con il tuo percorso) prima di attivare, oppure usa un percorso
> assoluto come
> `C:\path\SR-Support\.venv\Scripts\Activate.ps1` /
> `source /path/SR-Support/.venv/bin/activate`.
>
> Una volta attivata, puoi fare `cd` in qualsiasi sottocartella e `python` / `pip` / `pio`
> puntano ancora a quella `.venv`; ma i percorsi del tutorial `tools/...`, `firmware/...` e
> `hardware/v1/...` sono relativi, quindi **eseguili dalla cartella `SR-Support`**. La venv è
> vincolata al percorso in cui è stata creata: dopo aver spostato o rinominato il repository,
> elimina `.venv` e ricreala.

## 2.4 Strumenti di flash (per tutti i clienti - scegline uno)

Un'immagine precompilata è un unico bin da scrivere in flash a 0x0: **niente PlatformIO, nessun
download di toolchain**. Assicurati che il terminale sia nella cartella `SR-Support` e che il
prompt mostri `(.venv)`.

**A. GUI di Windows: Espressif Flash Download Tool**

1. Apri la pagina ufficiale "Other Tools" di Espressif e scarica Flash Download Tools:
   <https://www.espressif.com/en/support/download/other-tools>
2. Avvialo; seleziona **ESP32-S3**, carica
   `firmware/releases/sr_support_b_ptk_factory.bin` all'indirizzo `0x0`, scegli la porta e
   fai clic su **START**.

> Flash Download Tool è solo per Windows; su Linux/macOS usa esptool qui sotto.

**B. Windows / Linux / macOS: esptool (riga di comando)**

```bash
pip install esptool
```

Rete lenta in Cina: usa un mirror:

```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Scrivi in flash (`COM27` è la tua porta; Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`):

```bash
python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
```

Se la connessione fallisce, entra in modalità download: tieni premuto **BOOT**, premi **RST**,
rilascia **BOOT**.

## 2.5 PlatformIO (solo sviluppatori - build da sorgente)

> Salta questa sezione a meno che tu non modifichi il codice. **Nota**: PlatformIO (inclusa
> l'estensione PlatformIO per VS Code) scarica la piattaforma espressif32 e la toolchain Xtensa
> al primo utilizzo (~1 GB dal registry PlatformIO e da GitHub). Su molte reti in Cina è lento
> o fallisce e richiede un proxy/VPN; l'estensione per VS Code non evita il download.

Con il terminale nella cartella `SR-Support` e `(.venv)` attiva:

```bash
pip install platformio
```

Su Windows puoi anche eseguire `tools/install_platformio.ps1`, che installa nella stessa
`.venv`. Verifica:

```bash
pio --version
```

> Le versioni precedenti del tutorial installavano PlatformIO in una `.venv-pio` separata; ora
> vive nell'unica `.venv`. Se dopo l'aggiornamento `pio` non viene trovato, esegui
> `pip install platformio` nella `.venv` attivata (o riesegui `tools/install_platformio.ps1`);
> la vecchia `.venv-pio` può essere eliminata.

## 2.6 Strumenti lato computer e ambiente MuJoCo (gemello / azzeramento / log)

Non necessario per il flash. Installalo quando usi lo strumento di azzeramento con i tasti
freccia, il gemello digitale MuJoCo in tempo reale (`tools/live_twin.py`), il replay della
simulazione o gli strumenti di log. Con il terminale nella cartella `SR-Support` e `.venv`
attiva, installa le dipendenze (pyserial, numpy, MuJoCo 3.1+, gymnasium):

```bash
pip install -r tools/requirements.txt
```

Su Windows puoi anche eseguire `tools/install_tools_env.ps1` (crea/riusa `.venv` e installa lo
stesso set). Su una rete lenta in Cina aggiungi il mirror Tsinghua
`-i https://pypi.tuna.tsinghua.edu.cn/simple`; la prima installazione scarica qualche centinaio di MB.

**Verifica: esegui l'auto-test dell'ambiente (carica e fa avanzare MuJoCo, non solo importa)**

```bash
python tools/env_check.py
```

L'ultima riga deve essere `env check: PASS`, con un output simile a:

```text
[ok] mujoco 3.16.0
[ok] model hardware\v1\robot_v1.xml: nq=9 nv=8 dt=0.0002s, 200 steps stable ...
```

Senza scheda collegata, `[--] no serial port found` è informativo e non influisce sul PASS.

> Su Linux, un errore GLFW/OpenGL all'apertura della finestra MuJoCo indica librerie di sistema
> mancanti: installa `libgl1` e `libglew-dev` (ad es. `sudo apt install libgl1 libglew-dev`). I
> wheel MuJoCo per Windows/macOS includono il necessario. La simulazione e il replay di
> `training/b_line` usano lo stesso ambiente - niente da installare in più.

## 2.7 Collegare la scheda e confermare la porta seriale

1. Collega via USB-C; su Windows leggi il numero COM in Gestione periferiche, su Linux di solito
   è `/dev/ttyACM0` (aggiungi il tuo utente al gruppo `dialout`), su macOS di solito
   `/dev/tty.usbmodem*`;
2. ricorda la porta: ogni `COM27` nelle pagine successive è questo valore;
3. un monitor seriale o `hw_monitor.py` occupano la porta; chiudilo prima del flash.

## 2.8 Lista di controllo

- [ ] il terminale è nella **radice del repository** e il prompt mostra `(.venv)` (verifica con
      `pwd` / `Get-Location`);
- [ ] `firmware/releases/sr_support_b_ptk_factory.bin` esiste e si verifica
      (`sha256sum -c firmware/releases/SHA256SUMS`);
- [ ] `python -m esptool version` funziona, oppure Flash Download Tool si apre;
- [ ] la porta seriale della scheda è visibile;
- [ ] (sviluppatori) `pio --version` funziona;
- [ ] `python tools/env_check.py` stampa `env check: PASS`.

Prosegui solo quando gli elementi che ti servono sono soddisfatti.

---

[← Torna all'indice del tutorial](./index.md)
