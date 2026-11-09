---
title: 03 Flash del firmware principale
description: Scrivi in flash il firmware della linea B di SR-Support dal bin precompilato (Flash Download Tool / esptool) o compilalo con PlatformIO; comandi seriali e log di avvio.
---

# 03 Flash del firmware principale

> **Gli utenti di un'unità finita possono saltare questa pagina**: la fabbrica ha già caricato
> e verificato il firmware. Rifai questa procedura solo per aggiornamenti del firmware o dopo
> aver modificato il codice. I clienti usano l'immagine precompilata (3.1, senza PlatformIO);
> gli sviluppatori compilano da sorgente (3.2).

## 3.1 Scrivere in flash l'immagine precompilata (consigliato per i clienti)

1. Assicurati di avere `firmware/releases/sr_support_b_ptk_factory.bin` (somme di controllo in
   `SHA256SUMS` accanto);
2. entra in modalità download: tieni premuto **BOOT**, premi **RST**, rilascia **BOOT**;
3. scrivilo in flash (configurazione dello strumento alla [pagina 02, sezione 2.4](./02-environment.md); esegui questi comandi
   nella cartella `SR-Support` con `.venv` attivata):
   - GUI di Windows: Flash Download Tool → ESP32-S3 → carica il bin a `0x0` → START;
   - riga di comando Windows / Linux / macOS:

     ```bash
     python -m esptool --chip esp32s3 -p COM27 -b 460800 write_flash 0x0 firmware/releases/sr_support_b_ptk_factory.bin
     ```

4. al termine premi RST e leggi il log come in 3.3.

> Per il flash / debug seriale puoi alimentare l'ESP32 da USB e lasciare l'alimentazione 5 V solo
> ai servomotori (le due opzioni di alimentazione sono nella [pagina 04, sezione 4.4](./04-assembly.md)).

> Il comando è **identico su Windows / Linux / macOS**; cambia solo la porta:
> `COM27` su Windows, `/dev/ttyACM0` su Linux, `/dev/tty.usbmodem*` su macOS.
> Flash Download Tool è solo per Windows; altrove usa la riga di comando di esptool.

> La centratura in assemblaggio non richiede una seconda immagine: dopo aver scritto questa,
> accendi - entrambi i servomotori vanno allo zero del firmware (1681 / 1456 µs) - poi spegni e
> monta le squadrette ([pagina 04, sezione 4.2](./04-assembly.md)). Facoltativamente invia `e`
> per portarli prima al centro elettrico di 1520 µs (equivalente).

## 3.2 Compilare e scrivere in flash da sorgente (sviluppatori)

Ambiente: [pagina 02, sezione 2.5](./02-environment.md). Progetto:
`firmware/sr_support_b_ptk/` (ambiente `ptk7452`).

```bash
# Build
pio run -d firmware/sr_support_b_ptk

# Flash (replace COM27 with your port)
pio run -d firmware/sr_support_b_ptk -t upload --upload-port COM27
```

> Esegui questi comandi nella cartella `SR-Support` con `.venv` attivata (pagina 02, sezione 2.3);
> sono identici su tutte e tre le piattaforme - sostituisci `COM27` in `--upload-port` con la tua
> porta. Chiudi qualsiasi cosa occupi la porta seriale (monitor seriale, `tools/hw_monitor.py`)
> prima del flash, altrimenti ottieni `could not open port` / `Access is denied`.

Una build riuscita usa circa il 56% di RAM e il 30% di Flash (WiFi + web server inclusi; le
build precedenti senza WiFi erano circa 7% / 12%).

## 3.3 Monitor seriale

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Uguale su tutte e tre le piattaforme; sostituisci `COM27` con la tua porta.)

> **Assistente seriale con GUI per Windows (opzionale)**: UartAssist di 野人家园 (gratuito,
> singolo exe, solo Windows). Pagina ufficiale <https://cmsoft.cn/resource/101.html>, voce di
> download ufficiale <https://cmsoft.cn/resource/download/101>. Seleziona la porta COM,
> **115200, 8N1, nessun controllo di flusso**, abilita "invia nuova riga"; osserva il log di
> avvio/telemetria nel riquadro di ricezione e digita i comandi nella casella di invio.
> Scaricalo solo dal link ufficiale (i siti di terze parti spesso includono adware); non
> committare l'exe in questo repository.

**Visualizzatori di porta seriale per Linux / macOS (scegline uno)**:

- Preferito: il comando `pio device monitor` qui sopra (installato con il progetto, multipiattaforma);
- CLI leggera: `python -m serial.tools.miniterm /dev/ttyACM0 115200`
  (`/dev/tty.usbmodem*` su macOS; esci con `Ctrl-]`); funziona anche il
  `screen /dev/ttyACM0 115200` integrato (esci con `Ctrl-A`, poi `K`);
- GUI: **CoolTerm** (gratuito, Windows/macOS/Linux, sito ufficiale
  <https://freeware.the-meiers.org>); su Linux puoi anche `sudo apt install cutecom`.

> Su Linux aggiungi il tuo utente al gruppo `dialout`: `sudo usermod -aG dialout $USER`, poi esci
> e rientra.

Dopo aver aperto la porta, se la scheda è appena stata alimentata o hai premuto RST vedrai prima
il log di avvio; altrimenti premi RST una volta. Dopo il reset dovresti vedere:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up ... | w ... | q ... | qd ... | run
```

## 3.4 Comandi seriali (115200)

Digita ogni comando nella **casella di invio** del monitor/assistente seriale e premi Invio
(abilita "invia nuova riga" in UartAssist); il comando `m` richiede uno spazio e due valori, ad
es. `m 0.5 0`.

| Comando | Funzione |
|---|---|
| `g` | Avvia/continua l'esecuzione (questa build parte in automatico; di solito non serve) |
| `s` | Ferma l'esecutore, mantieni l'ultimo target |
| `x` | Rilascio di emergenza: stacca il PWM; riarma con `r` |
| `r` | Reinizializza il PWM e centra |
| `t` | Autotest dei servomotori (piccolo movimento) |
| `c` | Calibra giroscopio + **offset di zero dell'accelerometro** (il robot deve essere IN PIANO e fermo; memorizzato in NVS) |
| `m <q1> <q2>` | Target manuali dei giunti in rad |
| `1/2` | Spalla manuale ±0.5 rad |
| `3/4` | Gomito manuale ±0.5 rad |
| `0` | Neutro manuale |
| `l` | Log veloce a 50 Hz per 3 s |
| `k` | Stampa le larghezze d'impulso di centratura di entrambi i servomotori |
| `o` / `p` | Trim del centro della spalla ±10 µs |
| `z` | Zero in stile encoder: la posa attuale diventa q=0 per entrambi i giunti; stampa i nuovi impulsi (solo RAM; vedi [pagina 05](./05-zero-tool.md)) |
| `e` | Centro elettrico (opzionale): entrambi i servomotori a 1520 µs per montare le squadrette al centro elettrico; il modo usuale è accendere fino allo zero del firmware e montare lì (vedi [pagina 04, 4.2](./04-assembly.md)) |
| `d` | Attiva/disattiva il flusso a 50 Hz del gemello (gemello MuJoCo; lo stesso interruttore sulla pagina di stato) |
| `w` | Attiva/disattiva il WiFi (hotspot + pagina di stato/provisioning, vedi [pagina 08](./08-wifi.md)) |
| `v` / `b` | Inverti il segno di spalla / gomito |
| `i` / `j` | Inverti il segno X / Y dell'IMU |
| `h` | Attiva/disattiva l'homing in posizione eretta (percorso policy legacy) |
| `a` | Modalità di test di rialzata scriptata legacy |

## 3.5 Comportamento all'accensione

Il firmware definisce `AUTORUN_ON_BOOT`: dopo l'accensione l'esecutore attende che il robot sia
**completamente a terra e fermo** per 0.5 s, poi parte automaticamente - non serve `g`. Accendi
con il robot in posizione eretta.

---

[← Torna all'indice del tutorial](./index.md)
