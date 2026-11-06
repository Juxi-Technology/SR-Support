---
title: 07 Uso dell'auto-raddrizzamento e monitoraggio
description: Come usare SR-Support in ciascuna direzione di caduta, tempi di movimento previsti, eventi seriali e log di monitoraggio.
---

# 07 Uso dell'auto-raddrizzamento e monitoraggio

> Ogni unità finita viene collaudata in tutte e quattro le direzioni prima della spedizione. Per
> il primo uso, verifica comunque ogni direzione una volta secondo la sezione 7.2 per assicurarti
> che l'unità sia sana dopo il trasporto.

## 7.1 Procedura

1. Accendi con il robot in posizione eretta e attendi `autorun on: get-up waits for a fall`;
2. rovescia il robot in qualsiasi direzione, **lascialo e tienilo fermo per circa 0.5 s**;
3. quando appare `getup start pose=<pose>`, l'esecutore parte automaticamente;
4. in caso di successo il firmware stampa `standing -> executor done` e torna in attesa;
5. se una corsa supera i 14 s il firmware stampa `executor timeout`; dopo un cooldown di 1.5 s la
   soglia di caduta si riattiva e riprova.

## 7.2 Comportamento previsto per direzione

| Posa | Meccanismo | Tempo sul robot reale |
|---|---|---|
| `pitch_neg` (sommità → −X) | Il gomito si pianta, la corsa della spalla fa leva e solleva il corpo | ~3 s |
| `pitch_pos` (sommità → +X) | Stessa sollevata; se si ribalta durante la ritrazione, la ri-pianificazione della posa esegue di nuovo `pitch_pos` | ~5–6 s |
| `roll_pos` (sommità → −Y) | Leva diretta della spalla usando il lato a corsa lunga | ~3 s |
| `roll_neg` (sommità → +Y) | **Pressione diretta a corsa completa → pompaggi a cuneo del gomito ×2 → nuovo tentativo a colpo di frusta se necessario**; nessun ribaltamento | ~2–6 s |

> Il firmware precedente ribaltava `roll_neg` sopra la sommità e ri-pianificava su una sollevata
> pitch (5–14 s); la build attuale usa lo specchio della pressione +Y, quindi tutte e quattro le
> direzioni sono simmetriche e confrontabili in velocità. Un occasionale
> `executor re-plan roll_neg -> ...` significa solo che quella pressione è fallita ed è scattato
> il nuovo tentativo di fallback - è la normale rete di sicurezza.

## 7.3 Logica dell'esecutore (nel firmware)

- 20 tick (0.4 s) per waypoint di riferimento, interpolazione lineare; limite di velocità di
  variazione dell'uscita 0.08 rad/tick;
- dopo i waypoint, ritrae il braccio in posizione neutra a 0.033 rad/tick;
- completato quando `up_z > 0.95` con il target a zero per 50 tick;
- se il corpo si assesta su un altro asse sdraiato (`up_z<0.6`, `|ω|<0.8` per 15 tick), ritrae in
  neutro e passa alla sequenza di riferimento della nuova posa (fino a 5 cambi);
- la sequenza di riferimento `roll_neg` usa **mantenimenti adattivi per stadio**: gli stadi di
  pressione/pompaggio restano attivi finché `up_z<0.92` fino a un tetto di tick per stadio
  (pressione 40 / pompaggio 30 / pompaggio 30 / frusta 40 / finale 90); se il corpo si raddrizza
  a metà sequenza l'esecutore salta direttamente alla ritrazione, così gli stadi successivi non
  possono rovesciare il robot già in piedi.

## 7.4 Monitoraggio e log

```bash
python tools/hw_monitor.py COM27
```

(Eseguilo nella cartella `SR-Support` con `.venv` attivata - [pagina 02](./02-environment.md).
Chiudi prima qualsiasi assistente/monitor seriale; gli strumenti seriali / il download di
UartAssist per Windows sono alla [pagina 03, sezione 3.3](./03-build-flash.md).)

- Aggiunge eventi e riepiloghi di telemetria ogni 5 secondi a `logs/hw_monitor.log`;
- registra `getup start`, `executor re-plan`, `standing`, `executor timeout`, `IMU lost`, ecc.;
- controlla l'inviluppo dei servomotori (spalla `[-1.85,+1.82]`, gomito `±1.55`) e scrive `!! VIOLATION`;
- mentre l'esecutore gira stampa una traccia ogni 0.2 s:

```text
executor pose=roll_neg ph=3 tick=9 tgt=(2.00,-0.80) up=(0.58,-0.24,-0.77) q=(2.00,-0.80) sw=0
```

| Campo | Significato |
|---|---|
| `pose` | Sequenza di riferimento attuale |
| `ph` / `tick` | Fase del waypoint / tick nella fase |
| `tgt` | Angoli target dei giunti |
| `up` | Vettore up attuale |
| `q` | Comando attuale dei giunti |
| `sw` | Numero di cambi di posa finora |

> Aprire il monitor resetta l'ESP32; chiudilo prima del flash.

## 7.5 Tenuta dei registri

Per ogni test registra la posa, se è terminato con `done`, la durata, il numero di cambi e
qualsiasi violazione. `logs/hw_monitor.log` è il registro autorevole.

---

[← Torna all'indice del tutorial](./index.md)
