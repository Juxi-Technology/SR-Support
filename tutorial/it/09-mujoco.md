---
title: 09 Simulazione MuJoCo e il gemello in tempo reale
description: La finestra di simulazione MuJoCo locale (replay della rialzata sulle quattro pose), il gemello in tempo reale via WiFi del robot reale e il logging della telemetria.
---

# 09 Simulazione MuJoCo e il gemello in tempo reale

MuJoCo è usato in due modi in questo progetto, entrambi con `hardware/v1/robot_v1.xml` (il
modello della stessa sorgente del robot reale):

- **Simulazione locale**: senza robot collegato, ripeti in ciclo le quattro pose sdraiate e le
  relative rialzate sul computer per validare le sequenze di riferimento e osservare il movimento;
- **Gemello in tempo reale**: il robot reale trasmette il proprio assetto via WiFi e la finestra
  MuJoCo rispecchia il movimento reale in tempo reale (un gemello digitale).

La finestra funziona allo stesso modo in entrambi i casi: il trascinamento con il tasto sinistro
ruota la vista, quello con il tasto destro la sposta e la rotella esegue lo zoom. Prima del primo
uso, crea e attiva la `.venv` come alla [pagina 02](./02-environment.md) e installa al suo interno
le dipendenze degli strumenti (`pip install -r tools/requirements.txt`, vedi pagina 02).

## 9.1 Finestra di simulazione locale

Nella cartella `SR-Support` (`.venv` attivata):

```bash
python tools/play_getup_executor.py --xml hardware/v1/robot_v1.xml
```

La finestra ha come titolo `MuJoCo : sr_support_v1` (figura 9-1). Il robot viene collocato a
turno nelle quattro pose sdraiate (`roll_pos` → `roll_neg` → `pitch_pos` → `pitch_neg`); ogni
volta l'esecutore esegue la sequenza di riferimento con esattamente i parametri del firmware
finché il robot non è in piedi, poi viene impostata la posa successiva. Il ciclo si ripete finché
non chiudi la finestra. Il terminale stampa la posa e il risultato:

```text
--- cycle 1 pose 1/4 requested=roll_pos actual=roll_pos up=(+0.00,+1.00,-0.00)
    executor ok=True up=+1.00 servo=[0.0, -0.0] steps=113
```

`ok=True` significa che la posa si è rialzata nella simulazione. In caso di `ok=False`, verifica
la sequenza di riferimento e gli eventuali parametri modificati confrontandoli con la
[pagina 06](./06-debug-and-calibrate.md).

![Figura 9-1 La finestra di simulazione MuJoCo (replay della rialzata sulle quattro pose)](../images/sr-support/mujoco/01-mujoco-window.png)

*Figura 9-1: un fotogramma del ciclo delle quattro pose - l'esecutore rialza una posa sdraiata.*

> Differenza nota del modello: con il modello a massa 1x `roll_neg` stampa `ok=False` in
> simulazione (la massa/attrito del braccio del modello differiscono dal robot reale, vedi
> [pagina 11](./11-reference.md) 11.4); questo non influisce sul firmware reale.

## 9.2 Gemello in tempo reale via WiFi

Prerequisito: il robot si è unito alla rete domestica come alla [pagina 08](./08-wifi.md) e il
computer è sulla stessa rete. La pagina di stato mostra l'indirizzo del robot come `Robot IP`;
copialo nel comando seguente.

1. Nella pagina di stato premi `Twin ON` (come il comando seriale `d`);
2. nella cartella `SR-Support` con `.venv` attivata, esegui (sostituisci l'indirizzo con il
   `Robot IP` della pagina di stato):

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

Il modello rispecchia dal vivo l'assetto reale (flusso di quaternioni a 50 Hz) e mantiene il
corpo sul pavimento; il braccio è tenuto al suo angolo di contatto con il pavimento come il
servomotore in stallo, così non penetra mai il pavimento.

- Computer collegato direttamente all'hotspot del robot: l'indirizzo è sempre `192.168.4.1`,
  `python tools/live_twin.py --tcp 192.168.4.1:3333`;
- Alternativa via cavo: `python tools/live_twin.py --port COM27` (lo strumento invia `d` per
  attivare automaticamente il flusso);
- replay offline: `python tools/live_twin.py --replay logs/hw_fast_xxx.txt`;
- il gemello è di sola lettura, a parte l'attivazione/disattivazione del flusso: non invia mai
  comandi di controllo.

## 9.3 Logging della telemetria

```bash
python tools/tcp_log.py
```

Salva il flusso di telemetria in `logs/wifi_<time>.txt` per il replay offline (`--replay`) e
l'analisi dei guasti. Sull'hotspot si connette per impostazione predefinita a
`192.168.4.1:3333`; sulla rete domestica passa il `Robot IP` della pagina di stato:

```bash
python tools/tcp_log.py <Robot IP> 3333
```

## 9.4 Riferimenti per simulazione e addestramento

`training/b_line/` include l'esecutore, le sequenze di riferimento e l'ambiente di simulazione -
identici valore per valore al firmware - per replay, validazione e messa a punto dei parametri;
i file del modello sono descritti alla [pagina 11](./11-reference.md) 11.1.

---

[← Torna all'indice del tutorial](./index.md)
