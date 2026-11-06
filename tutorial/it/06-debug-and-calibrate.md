---
title: 06 Debug e calibrazione
description: Formato della telemetria, controlli di IMU e servomotori, calibrazione giroscopio+accelerometro, controllo della centratura, quattro pose sdraiate e soglia di caduta, criteri di completamento.
---

# 06 Debug e calibrazione

> **Gli utenti di un'unità finita possono saltare questa pagina**: la fabbrica calibra e verifica
> ogni unità. Rifai questi passaggi solo dopo aver sostituito un servomotore/IMU, rimontato una
> squadretta, oppure quando sospetti che un aggiornamento del firmware abbia alterato la
> calibrazione.

Questa è la **verifica funzionale e la calibrazione dell'intero robot** dopo assemblaggio, flash
e azzeramento; seguila in ordine prima di usare il robot.

> **Alimentazione durante il debug**: l'USB trasporta solo i dati seriali. `c` richiede solo l'IMU
> (i servomotori possono restare senza alimentazione); `t` / `z` / `e` richiedono la linea 5 V dei
> servomotori attiva. Se non vuoi che l'ESP32 sia alimentato da due fonti, scollega il ramo 5 V
> verso l'ESP32, alimentalo solo da USB e lascia che l'alimentatore 5 V alimenti solo i
> servomotori - una configurazione normale, vedi [pagina 04, sezione 4.4](./04-assembly.md).

## 6.1 Aprire la porta seriale e leggere la telemetria

Nella cartella `SR-Support` con `.venv` attivata, apri la porta seriale (`COM27` è la tua porta):

```bash
pio device monitor --rts 0 --dtr 0 -b 115200 -p COM27
```

(Gli strumenti seriali / il download di UartAssist per Windows sono alla
[pagina 03, sezione 3.3](./03-build-flash.md).)

Dopo aver aperto la porta, se la scheda è appena stata alimentata o hai premuto RST vedrai prima
il log di avvio; se non c'è log di avvio, premi RST una volta. Poi una riga di telemetria ogni
250 ms:

```text
IMU version 1.1.2
autorun on: get-up waits for a fall
up -0.01 +0.02 +1.00 | w  0.0  0.0  0.0 | q +0.00 +0.00 | qd  0.0  0.0 | run
```

| Campo | Significato | Come leggerlo |
|---|---|---|
| `up` | Vettore up del mondo in coordinate del corpo (x avanti, y sinistra, z su) | in posizione eretta `(0,0,1)`, inclinazione≈0°; pose sdraiate nel 6.5 (ad es. `(-1,0,0)`=pitch_pos) |
| `w` | Velocità angolare (rad/s) | ≈0 da fermo; non nulla durante rialzata/rotolamento; la soglia di caduta richiede `|w|<0.9` |
| `q` | Angoli **comandati** attuali dei giunti (spalla, gomito, rad; nessun feedback) | q=0 è braccio verticale; spalla + → braccio grande verso −Y, gomito + → avambraccio verso +X |
| `qd` | Velocità dei comandi dei giunti | raramente necessarie |
| `mode` | Modalità di esecuzione | `run` / `hold` / `manual` / `auto` |

Esempi di lettura (finestra `hw_watch`):

```text
up  x+0.00 y+0.00 z+1.00 tilt  0.0   # upright
up  x-1.00 y+0.00 z+0.00            # pitch_pos: top points +X
w   +0.0 +0.0 +0.0 rad/s |w| 0.0    # still
q   sh +0.00 el +0.00 mode hold     # arm vertical, idle
```

`tilt` è l'angolo tra il vettore up e la verticale (da `up_z`); 0° significa completamente eretto.

Se il flusso che scorre è difficile da leggere, usa la finestra live a righe fisse (i comandi
funzionano comunque):

```bash
python tools/hw_watch.py --port COM27
```

Ridisegna sul posto up/inclinazione, velocità angolare, angoli dei giunti, modalità e l'ultimo
evento; digita a `cmd>` e premi Invio per inviare un comando, e gli eventi vengono anche aggiunti
a `logs/hw_watch.log`. Per una rialzata completa in cui conta ogni riga grezza, continua a usare
`pio device monitor` o `tools/hw_monitor.py` (quest'ultimo scrive un riepilogo nel log ogni 5 s).

**Come inviare i comandi seriali**: tieni aperto il monitor e digita il comando seguito da Invio
(i comandi a carattere singolo non richiedono virgolette). Comandi usati in questa pagina:

```text
c        # gyro + accel calibration (robot level and still)
t        # servo self-test
k        # read both servo center pulses
m 0.5 0  # manual shoulder direction test
i / j    # flip IMU X / Y signs (only if a direction is reversed)
```

La tabella completa dei comandi è alla [pagina 03, sezione 3.4](./03-build-flash.md).

**Script di auto-verifica rapida** (chiudi prima il monitor seriale per liberare la porta):

```bash
python tools/hw_check.py --port COM27
python tools/hw_check.py --port COM27 --tilt 8
```

Il primo comando legge 0.6 s di telemetria; durante `--tilt 8` inclina il robot a mano e stampa
gli intervalli di up/giroscopio e l'intervallo di inclinazione, il che rivela un'IMU bloccata o
orientata male.

## 6.2 Controlli e calibrazione dell'IMU

`c` fa due cose:

1. **Bias di zero del giroscopio**: media 200 campioni da fermo (circa 2 s) nell'offset di
   velocità zero; viene usato per il ciclo di alimentazione corrente e rifatto automaticamente a
   ogni avvio;
2. **Zero dell'accelerometro**: dagli stessi campioni media il vettore di gravità, richiedendo che
   il robot sia in piano (gravità interamente su +Z), lo verifica e lo memorizza in NVS
   (ricaricato all'avvio).

Procedura (l'alimentazione dei servomotori non è necessaria):

1. esegui prima la verifica dell'orientamento meccanico alla [pagina 04, sezione 4.5](./04-assembly.md)
   (albero della spalla verso −Y dell'IMU, albero del gomito verso +X dell'IMU);
2. metti il robot in piedi su un tavolo **in piano**, senza mani addosso, con i cavi che non tirano;
3. digita `c` e premi Invio nel monitor seriale o nel `cmd>` di `hw_watch`:

   ```text
   c
   ```

4. resta fermo per circa 2 s; in caso di successo stampa:

   ```text
   gyro bias (rad/s): ...
   accel bias (m/s^2): ... (saved)
   calibration done; hold
   ```

5. `accel cal rejected: |a|=...` significa che il robot non era in piano o non era fermo (la norma
   della gravità si discosta di oltre 1.5 m/s² da 9.8); il bias resta invariato - riposizionalo e
   invia di nuovo `c`.

Verifica:

- inclina lentamente a sinistra/destra e avanti/indietro: le componenti x/y di `up` devono seguire
  con continuità; se una direzione è invertita, invia `i` / `j` per invertire il segno dell'asse
  dell'IMU ed esegui di nuovo `c`;
- appoggia il robot e attendi 2 s: `up` deve corrispondere alla tabella delle pose sdraiate del 6.5
  (ad es. `(0,-1,0)` = roll_neg) con la faccia della base piatta;
- un'inclinazione persistente di 5°+ da sdraiato di solito significa che lo zero
  dell'accelerometro è fuori taratura - rifai questa sezione.

> Le unità finite sono calibrate in fabbrica (memorizzate in NVS); rifai questo solo dopo aver
> sostituito/rimontato l'IMU o quando la posa sdraiata è visibilmente inclinata. `c` calibra solo
> l'IMU - non cambia lo zero dei servomotori (quello è la [pagina 05](./05-zero-tool.md)).
>
> Se hai usato comandi manuali prima di calibrare (la telemetria termina con `manual`), `c` lascia
> il robot in `hold`/`manual` e la soglia di caduta non avvierà una rialzata; tienilo in piedi e
> invia `g` per riprendere, oppure resetta la scheda.

## 6.3 Controlli dei servomotori e autotest delle direzioni

| Controllo | Metodo | Atteso |
|---|---|---|
| Centri | `k` | `centers: shoulder 1681 us, elbow 1456 us` (valori del centro visivo memorizzati 2026-11; riazzera secondo la [pagina 05](./05-zero-tool.md)) |
| Trim della spalla | `o` / `p` (±10 µs) | Braccio verticale a `q=0` |
| Direzione | `m 0.5 0` / `m 0 0.5` | Spalla + → braccio grande verso −Y; gomito + → avambraccio verso +X |
| Inversione di segno | `v` (spalla) / `b` (gomito) | Solo se una direzione è invertita |
| Autotest | `t` | Piccolo movimento su entrambi i giunti, poi centratura |
| Neutro | `m 0 0` o `r` | Braccio verticale |

Limiti dei giunti:

- comandi manuali della spalla `[-1.85, +1.82]` rad; gomito meccanico `±1.55` rad (raggiungibile
  dall'esecutore);
- i comandi manuali `m` limitano il gomito a `[-0.90, +0.70]` rad;
- uscita PWM 500–2500 µs a 50 Hz.

Digita questi uno alla volta nella **casella di invio** del monitor/assistente seriale (Invio
dopo ciascuno):

```text
t
k
m 0.5 0
m 0 0.5
m 0 0
```

Conferma: spalla `q>0` → braccio grande verso **−Y**; gomito `q>0` → avambraccio verso **+X**.
Direzione sbagliata: inverti con `v` / `b`, oppure rimonta la squadretta.

## 6.4 Controllo della centratura

Memorizzata in fabbrica (spalla 1681 µs / gomito 1456 µs) - **saltabile per un'unità di serie**. In
una build fai-da-te è già stata fatta con l'[azzeramento della pagina 05](./05-zero-tool.md) e i
valori sono stati incorporati in `config.h` (riscrivi il firmware se sono cambiati); qui basta
eseguire `k` per confermare che i centri corrispondano ai valori memorizzati. Torna alla pagina 05
solo dopo aver re-indicizzato una squadretta, riassemblato, o se il braccio non si ferma più al
centro visivo.

## 6.5 Quattro pose sdraiate e soglia di caduta

| Posa | `up` del monitor | Significato fisico |
|---|---|---|
| `pitch_pos` | `(-1, 0, 0)` | La sommità del corpo punta verso +X |
| `pitch_neg` | `(+1, 0, 0)` | La sommità del corpo punta verso −X |
| `roll_pos` | `(0, +1, 0)` | La sommità del corpo punta verso −Y |
| `roll_neg` | `(0, -1, 0)` | La sommità del corpo punta verso +Y |

Condizione della soglia di caduta (firmware):

```text
up_z < 0.30 and |ω| < 0.9 rad/s for 25 consecutive ticks (0.5 s)
```

Solo allora stampa `getup start pose=...` e inizia. Quindi posiziona il robot, lascialo e tienilo
fermo per ~0.5 s; agitarlo subito dopo averlo posato di solito significa che una mano lo sta
ancora toccando o che il corpo sta ancora rotolando.

Verifica: posiziona il robot in ciascuna delle quattro pose, lascialo e tienilo fermo; entro 0.5 s
il log seriale deve mostrare `getup start pose=<matching pose>`.

## 6.6 Criteri di completamento

- [ ] `c` stampa `accel bias ... (saved)`;
- [ ] `t` mostra direzioni corrette su entrambi i giunti;
- [ ] `k` corrisponde ai centri memorizzati (o hai riazzerato secondo la pagina 05 e memorizzato);
- [ ] tutte e quattro le pose sdraiate avviano `getup start`.

---

[← Torna all'indice del tutorial](./index.md)
