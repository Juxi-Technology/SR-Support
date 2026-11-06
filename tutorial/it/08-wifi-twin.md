---
title: 08 WiFi e il gemello della simulazione
description: Pagina di stato, provisioning della rete domestica, il gemello digitale MuJoCo wireless e il logging della telemetria WiFi.
---

# 08 WiFi e il gemello della simulazione

Questo passo è opzionale e non necessario per l'auto-raddrizzamento in sé.

## 8.1 Hotspot e pagina di stato

Hotspot: SSID `SR-Support`, password `srsupport`, indirizzo `192.168.4.1` (`w` lo attiva/disattiva;
attivo per impostazione predefinita all'avvio). `w` si invia via seriale: digita `w` nella casella
di invio del monitor/assistente seriale e premi Invio; gli strumenti seriali / il download di
UartAssist per Windows sono alla [pagina 03, sezione 3.3](./03-build-flash.md).

Unisciti all'hotspot e apri `http://192.168.4.1` (i telefoni di solito aprono il portale
automaticamente). La pagina si aggiorna ogni 300 ms: stato, vettore up e barra di verticalità,
comandi dei giunti, posa/fase di rialzata, stato del WiFi domestico e interruttore del flusso del
gemello. Se il browser usa un proxy, aggiungi un'eccezione per questo indirizzo.

## 8.2 Provisioning (unirsi al WiFi domestico)

Nella pagina di stato usa la scheda Home WiFi: `Scan` → scegli una rete → inserisci la password →
`Connect`. In caso di successo l'ESP32 funziona in AP+STA:

- l'hotspot resta attivo (il lavoro in banco non è influenzato);
- il robot è raggiungibile sulla LAN domestica (la pagina mostra il suo `Robot IP`);
- le credenziali sono memorizzate in NVS e la connessione viene ripristinata automaticamente
  all'avvio.

Solo 2.4 GHz; scansioni/connessioni vengono rifiutate mentre è in corso una rialzata.

## 8.3 Gemello digitale MuJoCo wireless in tempo reale

Premi `Twin ON` sulla pagina di stato (come il comando seriale `d`), poi:

```bash
python tools/live_twin.py --tcp <Robot IP>:3333
```

(Nella cartella `SR-Support`; crea e attiva prima `.venv` come alla
[pagina 02](./02-environment.md) - anche l'ambiente degli strumenti è configurato lì.)

- La finestra rispecchia dal vivo l'assetto reale e mantiene il corpo sul pavimento;
- il braccio è mantenuto al suo angolo di contatto con il pavimento come il servomotore in stallo
  (nessuna penetrazione del pavimento);
- il cavo USB serve solo per il flash e per scaricare i log;
- riproduci offline un log registrato con `--replay <file>`.

## 8.4 Logging della telemetria WiFi

```bash
python tools/tcp_log.py
```

Salva il flusso di telemetria dell'hotspot in `logs/wifi_<time>.txt` per replay e analisi offline.

## 8.5 Riferimenti per simulazione e addestramento

Il repository include il modello MuJoCo e il codice di addestramento (`training/b_line/`) per
replay e riaddestramento; i file del modello sono descritti alla [pagina 10](./10-reference.md).

---

[← Torna all'indice del tutorial](./index.md)
